"""OpenAI Responses API client with retry and safe error handling."""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass
from typing import Any
from urllib.parse import urlparse

import requests

from .config import PluginConfig

logger = logging.getLogger(__name__)


class APIError(RuntimeError):
    """Raised when OpenAI API request fails."""


@dataclass(frozen=True)
class GeneratedAnswer:
    """Unified generated response content from OpenAI."""

    text: str
    raw_response_id: str | None
    model: str | None


class OpenAIResponsesClient:
    """Thin synchronous OpenAI Responses API client."""

    def __init__(
        self,
        session: requests.Session,
        timeout_seconds: float = 10.0,
        max_retries: int = 2,
        retry_backoff_seconds: float = 0.4,
    ) -> None:
        self.session = session
        self.timeout_seconds = timeout_seconds
        self.max_retries = max_retries
        self.retry_backoff_seconds = retry_backoff_seconds
        self._models_cache: dict[str, tuple[float, list[str]]] = {}

    def generate(self, prompt: str, config: PluginConfig, correlation_id: str) -> GeneratedAnswer:
        """Call Responses API and return extracted output text."""
        payload = self._build_payload(prompt=prompt, config=config)
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {config.api_key}",
        }

        last_error: Exception | None = None
        for attempt in range(1, self.max_retries + 2):
            try:
                response = self.session.post(
                    config.endpoint_url,
                    headers=headers,
                    json=payload,
                    timeout=self.timeout_seconds,
                )
                if response.status_code >= 500 and attempt <= self.max_retries:
                    self._sleep_before_retry(attempt)
                    continue
                if response.status_code >= 400:
                    raise APIError(self._extract_api_error(response))
                data = response.json()
                return self._parse_generated_answer(data)
            except (requests.Timeout, requests.ConnectionError) as exc:
                last_error = exc
                if attempt > self.max_retries:
                    break
                logger.warning(
                    "[%s] transient network error on attempt %s/%s: %s",
                    correlation_id,
                    attempt,
                    self.max_retries + 1,
                    str(exc),
                )
                self._sleep_before_retry(attempt)
            except ValueError as exc:
                raise APIError("Не удалось разобрать JSON-ответ OpenAI") from exc

        raise APIError(f"Сетевой сбой при запросе к OpenAI: {last_error}")

    def _build_payload(self, prompt: str, config: PluginConfig) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "model": config.model,
            "input": [
                {"role": "developer", "content": config.system_prompt},
                {"role": "user", "content": prompt},
            ],
            "max_output_tokens": config.max_output_tokens,
            "temperature": config.temperature,
            "top_p": config.top_p,
            "frequency_penalty": config.frequency_penalty,
            "presence_penalty": config.presence_penalty,
            "text": {"verbosity": config.verbosity},
            "reasoning": {"effort": config.reasoning_effort},
        }
        return payload

    def _parse_generated_answer(self, data: dict[str, Any]) -> GeneratedAnswer:
        response_id = _as_optional_str(data.get("id"))
        model = _as_optional_str(data.get("model"))
        output_text = _as_optional_str(data.get("output_text"))
        if output_text:
            return GeneratedAnswer(text=output_text, raw_response_id=response_id, model=model)

        extracted = _extract_text_from_output(data.get("output"))
        if not extracted:
            raise APIError("OpenAI вернул пустой ответ")
        return GeneratedAnswer(text=extracted, raw_response_id=response_id, model=model)

    def _extract_api_error(self, response: requests.Response) -> str:
        status = response.status_code
        try:
            data = response.json()
        except ValueError:
            return f"HTTP {status}: {response.text[:400]}"

        if isinstance(data, dict):
            err = data.get("error")
            if isinstance(err, dict):
                msg = err.get("message")
                if isinstance(msg, str) and msg.strip():
                    return f"HTTP {status}: {msg}"
        return f"HTTP {status}: {str(data)[:400]}"

    def _sleep_before_retry(self, attempt: int) -> None:
        time.sleep(self.retry_backoff_seconds * (2 ** (attempt - 1)))

    def list_models(self, config: PluginConfig, correlation_id: str) -> list[str]:
        """Return model IDs visible to the provided API key."""
        cache_key = f"{config.endpoint_url}|{config.api_key}"
        cached = self._models_cache.get(cache_key)
        if cached and cached[0] > time.time():
            return cached[1]

        endpoint = _derive_models_endpoint(config.endpoint_url)
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {config.api_key}",
        }
        try:
            response = self.session.get(
                endpoint,
                headers=headers,
                timeout=min(self.timeout_seconds, 8.0),
            )
        except (requests.Timeout, requests.ConnectionError) as exc:
            raise APIError(f"Не удалось получить список моделей: {exc}") from exc

        if response.status_code >= 400:
            raise APIError(self._extract_api_error(response))
        try:
            payload = response.json()
        except ValueError as exc:
            raise APIError("OpenAI вернул некорректный JSON списка моделей") from exc

        if not isinstance(payload, dict) or not isinstance(payload.get("data"), list):
            raise APIError("Неожиданный формат ответа /v1/models")

        models: list[str] = []
        for row in payload["data"]:
            if isinstance(row, dict):
                model_id = row.get("id")
                if isinstance(model_id, str) and model_id.strip():
                    models.append(model_id)
        models = sorted(set(models))
        self._models_cache[cache_key] = (time.time() + 300.0, models)
        logger.debug("[%s] models fetched: %s", correlation_id, len(models))
        return models


def _as_optional_str(value: Any) -> str | None:
    return value if isinstance(value, str) and value.strip() else None


def _extract_text_from_output(output: Any) -> str:
    if not isinstance(output, list):
        return ""

    chunks: list[str] = []
    for item in output:
        if not isinstance(item, dict):
            continue

        if isinstance(item.get("text"), str):
            chunks.append(item["text"])

        content = item.get("content")
        if isinstance(content, list):
            for part in content:
                if not isinstance(part, dict):
                    continue
                text = part.get("text")
                if isinstance(text, str) and text.strip():
                    chunks.append(text)
    return "\n".join([chunk for chunk in chunks if chunk.strip()]).strip()


def _derive_models_endpoint(responses_endpoint: str) -> str:
    parsed = urlparse(responses_endpoint)
    if not parsed.scheme or not parsed.netloc:
        return "https://api.openai.com/v1/models"

    path = parsed.path or "/v1/responses"
    if "/v1/" in path:
        prefix = path.split("/v1/")[0]
        return f"{parsed.scheme}://{parsed.netloc}{prefix}/v1/models"
    base = path.rsplit("/", 1)[0] if "/" in path else ""
    return f"{parsed.scheme}://{parsed.netloc}{base}/models"
