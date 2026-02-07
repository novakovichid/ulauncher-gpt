from __future__ import annotations

from ulauncher_gpt.config import PluginConfig
from ulauncher_gpt.extension import GPTExtension, KeywordQueryEventListener
from ulauncher_gpt.openai_client import APIError, GeneratedAnswer


class _Event:
    def __init__(self, argument: str | None):
        self.argument = argument

    def get_argument(self):
        return self.argument


class _StubClient:
    def __init__(
        self,
        result: GeneratedAnswer | None = None,
        err: Exception | None = None,
        models: list[str] | None = None,
    ):
        self.result = result
        self.err = err
        self.models = models if models is not None else ["gpt-4.1-mini"]
        self.last_model: str | None = None

    def generate(self, prompt: str, config: PluginConfig, correlation_id: str):
        if self.err:
            raise self.err
        self.last_model = config.model
        return self.result

    def list_models(self, config: PluginConfig, correlation_id: str) -> list[str]:
        if self.err:
            raise self.err
        return self.models


class _ExtensionCtx:
    def __init__(self, preferences: dict[str, str]):
        self.preferences = preferences


def _prefs() -> dict[str, str]:
    return {
        "api_key": "sk-test",
        "model": "gpt-4.1-mini",
        "endpoint_url": "https://api.openai.com/v1/responses",
        "system_prompt": "test",
        "temperature": "1",
        "max_completion_tokens": "100",
        "top_p": "1",
        "frequency_penalty": "0",
        "presence_penalty": "0",
        "line_wrap": "50",
        "verbosity": "low",
        "reasoning_effort": "minimal",
        "locale": "ru",
    }


def test_extension_initializes_subscription() -> None:
    ext = GPTExtension()
    assert len(ext._subscriptions) == 1


def test_listener_returns_empty_prompt_action() -> None:
    listener = KeywordQueryEventListener(_StubClient())
    action = listener.on_event(_Event(""), _ExtensionCtx(_prefs()))
    assert len(action.items) == 1
    assert "Введите" in action.items[0].name


def test_listener_handles_api_error() -> None:
    listener = KeywordQueryEventListener(_StubClient(err=APIError("boom")))
    action = listener.on_event(_Event("hello"), _ExtensionCtx(_prefs()))
    assert len(action.items) == 1
    assert "ошибка" in action.items[0].name.lower()


def test_listener_success_action_contains_encoded_links() -> None:
    listener = KeywordQueryEventListener(
        _StubClient(
            result=GeneratedAnswer(text="answer", raw_response_id="r1", model="gpt-4.1-mini")
        )
    )
    action = listener.on_event(_Event("a b+c"), _ExtensionCtx(_prefs()))
    assert len(action.items) == 4
    assert "a+b%2Bc" in action.items[1].on_enter.url
    assert "a+b%2Bc" in action.items[2].on_enter.url


def test_listener_models_command_returns_models_list() -> None:
    listener = KeywordQueryEventListener(_StubClient(models=["gpt-4.1-mini", "gpt-4.1"]))
    action = listener.on_event(_Event("/models"), _ExtensionCtx(_prefs()))
    assert "Доступные модели" in action.items[0].name
    assert action.items[1].name.startswith("gpt-4.1 | Tier 1 | $2/1M in")


def test_listener_use_model_and_clear_model() -> None:
    client = _StubClient(
        result=GeneratedAnswer(text="answer", raw_response_id="r1", model="gpt-4.1-mini"),
        models=["gpt-4.1", "gpt-4.1-mini"],
    )
    listener = KeywordQueryEventListener(client)
    set_action = listener.on_event(_Event("/use-model gpt-4.1"), _ExtensionCtx(_prefs()))
    assert "Runtime-модель обновлена" in set_action.items[0].name

    listener.on_event(_Event("hello"), _ExtensionCtx(_prefs()))
    assert client.last_model == "gpt-4.1"

    clear_action = listener.on_event(_Event("/clear-model"), _ExtensionCtx(_prefs()))
    assert "сброшена" in clear_action.items[0].name


def test_listener_use_model_rejects_unavailable() -> None:
    listener = KeywordQueryEventListener(_StubClient(models=["gpt-4.1-mini"]))
    action = listener.on_event(_Event("/use-model gpt-4.1"), _ExtensionCtx(_prefs()))
    assert "недоступна" in action.items[0].description
