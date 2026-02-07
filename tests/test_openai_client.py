from __future__ import annotations

import pytest
import requests

from ulauncher_gpt.config import PluginConfig
from ulauncher_gpt.openai_client import APIError, OpenAIResponsesClient


class _FakeResponse:
    def __init__(self, status_code: int, payload=None, text: str = "") -> None:
        self.status_code = status_code
        self._payload = payload
        self.text = text

    def json(self):
        if isinstance(self._payload, Exception):
            raise self._payload
        return self._payload


class _FakeSession:
    def __init__(self, outputs):
        self.outputs = outputs
        self.calls = 0

    def post(self, *args, **kwargs):
        out = self.outputs[self.calls]
        self.calls += 1
        if isinstance(out, Exception):
            raise out
        return out

    def get(self, *args, **kwargs):
        out = self.outputs[self.calls]
        self.calls += 1
        if isinstance(out, Exception):
            raise out
        return out


def _config() -> PluginConfig:
    return PluginConfig.from_preferences(
        {
            "api_key": "sk-test",
            "model": "gpt-4.1-mini",
            "endpoint_url": "https://api.openai.com/v1/responses",
            "system_prompt": "x",
            "temperature": "1",
            "max_completion_tokens": "50",
            "top_p": "1",
            "frequency_penalty": "0",
            "presence_penalty": "0",
            "line_wrap": "50",
            "verbosity": "low",
            "reasoning_effort": "minimal",
        }
    )


def test_generate_reads_output_text() -> None:
    session = _FakeSession(
        [_FakeResponse(200, {"id": "r1", "model": "gpt-5", "output_text": "hello"})]
    )
    client = OpenAIResponsesClient(session=session, retry_backoff_seconds=0)
    answer = client.generate("ping", _config(), correlation_id="cid")
    assert answer.text == "hello"
    assert answer.raw_response_id == "r1"


def test_generate_fallback_output_parser() -> None:
    payload = {
        "output": [
            {
                "content": [
                    {"type": "output_text", "text": "line1"},
                    {"type": "output_text", "text": "line2"},
                ]
            }
        ]
    }
    session = _FakeSession([_FakeResponse(200, payload)])
    client = OpenAIResponsesClient(session=session, retry_backoff_seconds=0)
    answer = client.generate("ping", _config(), correlation_id="cid")
    assert answer.text == "line1\nline2"


def test_generate_retries_on_timeout_then_succeeds() -> None:
    session = _FakeSession(
        [
            requests.Timeout("slow"),
            _FakeResponse(200, {"output_text": "ok"}),
        ]
    )
    client = OpenAIResponsesClient(session=session, retry_backoff_seconds=0)
    answer = client.generate("ping", _config(), correlation_id="cid")
    assert answer.text == "ok"
    assert session.calls == 2


def test_generate_raises_on_http_error() -> None:
    session = _FakeSession([_FakeResponse(401, {"error": {"message": "bad key"}})])
    client = OpenAIResponsesClient(session=session, retry_backoff_seconds=0)
    with pytest.raises(APIError) as exc:
        client.generate("ping", _config(), correlation_id="cid")
    assert "bad key" in str(exc.value)


def test_generate_raises_on_malformed_json() -> None:
    session = _FakeSession([_FakeResponse(200, ValueError("bad json"))])
    client = OpenAIResponsesClient(session=session, retry_backoff_seconds=0)
    with pytest.raises(APIError):
        client.generate("ping", _config(), correlation_id="cid")


def test_list_models_returns_sorted_ids() -> None:
    session = _FakeSession(
        [
            _FakeResponse(
                200,
                {"data": [{"id": "gpt-5-mini"}, {"id": "gpt-5"}, {"id": "gpt-5-mini"}]},
            )
        ]
    )
    client = OpenAIResponsesClient(session=session, retry_backoff_seconds=0)
    models = client.list_models(_config(), correlation_id="cid")
    assert models == ["gpt-5", "gpt-5-mini"]


def test_payload_for_gpt41_family_uses_sampling_and_penalties() -> None:
    client = OpenAIResponsesClient(session=_FakeSession([]), retry_backoff_seconds=0)
    payload = client._build_payload("ping", _config())
    assert "temperature" in payload
    assert "top_p" in payload
    assert "frequency_penalty" in payload
    assert "presence_penalty" in payload
    assert "reasoning" not in payload
    assert "text" not in payload


def test_payload_for_gpt4o_mini_uses_sampling_and_penalties() -> None:
    client = OpenAIResponsesClient(session=_FakeSession([]), retry_backoff_seconds=0)
    config = PluginConfig.from_preferences(
        {
            "api_key": "sk-test",
            "model": "gpt-4o-mini",
            "endpoint_url": "https://api.openai.com/v1/responses",
            "system_prompt": "x",
            "temperature": "1",
            "max_completion_tokens": "50",
            "top_p": "1",
            "frequency_penalty": "0",
            "presence_penalty": "0",
            "line_wrap": "50",
            "verbosity": "high",
            "reasoning_effort": "medium",
        }
    )
    payload = client._build_payload("ping", config)
    assert "temperature" in payload
    assert "top_p" in payload
    assert "frequency_penalty" in payload
    assert "presence_penalty" in payload
    assert "reasoning" not in payload
    assert "text" not in payload


def test_payload_for_gpt5_family_uses_reasoning_and_verbosity() -> None:
    client = OpenAIResponsesClient(session=_FakeSession([]), retry_backoff_seconds=0)
    config = PluginConfig.from_preferences(
        {
            "api_key": "sk-test",
            "model": "custom",
            "custom_model": "gpt-5-mini",
            "endpoint_url": "https://api.openai.com/v1/responses",
            "system_prompt": "x",
            "temperature": "1",
            "max_completion_tokens": "50",
            "top_p": "1",
            "frequency_penalty": "0",
            "presence_penalty": "0",
            "line_wrap": "50",
            "verbosity": "high",
            "reasoning_effort": "medium",
        }
    )
    payload = client._build_payload("ping", config)
    assert "reasoning" in payload
    assert "text" in payload
    assert "temperature" not in payload
    assert "top_p" not in payload
    assert "frequency_penalty" not in payload
