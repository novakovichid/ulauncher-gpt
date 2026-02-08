"""Ulauncher entry integration and event handling."""

from __future__ import annotations

import logging
from dataclasses import replace
from typing import Any

import requests
from ulauncher.api.client.EventListener import EventListener
from ulauncher.api.client.Extension import Extension
from ulauncher.api.shared.event import KeywordQueryEvent

from .config import ConfigError, PluginConfig
from .openai_client import APIError, OpenAIResponsesClient
from .presenters import (
    empty_prompt_action,
    error_action,
    info_action,
    models_action,
    success_action,
)
from .utils import mask_secret, new_correlation_id

logger = logging.getLogger(__name__)
ASK_PREFIX = "/ask "


class GPTExtension(Extension):
    """Ulauncher extension that calls OpenAI Responses API."""

    def __init__(self) -> None:
        super().__init__()
        self.session = requests.Session()
        self.client = OpenAIResponsesClient(self.session)
        self.subscribe(KeywordQueryEvent, KeywordQueryEventListener(self.client))
        logger.info("Ulauncher GPT extension started")


class KeywordQueryEventListener(EventListener):
    """Handles keyword query events from Ulauncher."""

    def __init__(self, client: OpenAIResponsesClient) -> None:
        self.client = client
        self._selected_model: str | None = None

    def on_event(self, event: Any, extension: Any) -> Any:
        """Validate input, call OpenAI, and return a result list action."""
        correlation_id = new_correlation_id()
        search_term = (event.get_argument() or "").strip()

        try:
            config = PluginConfig.from_preferences(extension.preferences)
        except ConfigError as exc:
            logger.error("[%s] config parse failed: %s", correlation_id, str(exc))
            return error_action("ru", str(exc))

        if config.debug_mode:
            logger.debug(
                "[%s] request config: model=%s endpoint=%s api_key=%s",
                correlation_id,
                config.model,
                config.endpoint_url,
                mask_secret(config.api_key),
            )

        if not search_term:
            return empty_prompt_action(config.locale)

        if search_term == "/models":
            try:
                models = self.client.list_models(config=config, correlation_id=correlation_id)
            except APIError as exc:
                logger.error("[%s] models list failed: %s", correlation_id, str(exc))
                return error_action(config.locale, str(exc))
            return models_action(config.locale, models, active_model=self._selected_model)

        if search_term.startswith("/use-model "):
            model_id = search_term.replace("/use-model ", "", 1).strip()
            if not model_id:
                return error_action(config.locale, "Использование: /use-model <model_id>")
            try:
                models = self.client.list_models(config=config, correlation_id=correlation_id)
            except APIError as exc:
                logger.error("[%s] models list failed: %s", correlation_id, str(exc))
                return error_action(config.locale, str(exc))
            if model_id not in models:
                return error_action(
                    config.locale,
                    f"Модель '{model_id}' недоступна для этого API-ключа. Используйте /models",
                )
            self._selected_model = model_id
            return info_action(
                title="Runtime-модель обновлена",
                message=f"Выбрана модель: {model_id}. Сброс: /clear-model",
            )

        if search_term == "/clear-model":
            self._selected_model = None
            return info_action(
                title="Runtime-модель сброшена",
                message="Теперь используется модель из настроек плагина.",
            )

        prompt_text = ""
        if search_term.startswith(ASK_PREFIX):
            prompt_text = search_term.replace(ASK_PREFIX, "", 1).strip()
            if not prompt_text:
                return error_action(config.locale, "Использование: /ask <текст запроса>")
        elif search_term.startswith("/"):
            return info_action(
                title="Неизвестная команда",
                message="Доступные команды: /ask, /models, /use-model, /clear-model",
            )
        else:
            return info_action(
                title="Ручной запуск включен",
                message="Для отправки в OpenAI используйте: /ask <текст>",
                clipboard=f"/ask {search_term}",
            )

        try:
            effective_config = (
                replace(config, model=self._selected_model)
                if self._selected_model is not None
                else config
            )
            generated = self.client.generate(
                prompt=prompt_text,
                config=effective_config,
                correlation_id=correlation_id,
            )
        except APIError as exc:
            logger.error("[%s] OpenAI API error: %s", correlation_id, str(exc))
            return error_action(config.locale, str(exc))
        except Exception as exc:  # pragma: no cover - final safety net for UI stability
            logger.exception("[%s] Unexpected error", correlation_id)
            return error_action(config.locale, f"Непредвиденная ошибка: {exc}")

        return success_action(
            locale=config.locale,
            answer=generated.text,
            prompt=prompt_text,
            line_wrap=config.line_wrap,
        )
