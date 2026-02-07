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
    def __init__(self, result: GeneratedAnswer | None = None, err: Exception | None = None):
        self.result = result
        self.err = err

    def generate(self, prompt: str, config: PluginConfig, correlation_id: str):
        if self.err:
            raise self.err
        return self.result


class _ExtensionCtx:
    def __init__(self, preferences: dict[str, str]):
        self.preferences = preferences


def _prefs() -> dict[str, str]:
    return {
        "api_key": "sk-test",
        "model": "gpt-5",
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
        _StubClient(result=GeneratedAnswer(text="answer", raw_response_id="r1", model="gpt-5"))
    )
    action = listener.on_event(_Event("a b+c"), _ExtensionCtx(_prefs()))
    assert len(action.items) == 3
    assert "a+b%2Bc" in action.items[1].on_enter.url
    assert "a+b%2Bc" in action.items[2].on_enter.url
