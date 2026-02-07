import pytest

from ulauncher_gpt.config import ConfigError, PluginConfig


def _base_preferences() -> dict[str, str]:
    return {
        "api_key": "sk-test",
        "model": "gpt-5",
        "custom_model": "",
        "endpoint_url": "https://api.openai.com/v1/responses",
        "system_prompt": "test",
        "temperature": "1",
        "max_completion_tokens": "500",
        "top_p": "1",
        "frequency_penalty": "0",
        "presence_penalty": "0",
        "line_wrap": "50",
        "verbosity": "low",
        "reasoning_effort": "minimal",
        "debug_mode": "false",
        "locale": "ru",
    }


def test_config_parses_valid_preferences() -> None:
    config = PluginConfig.from_preferences(_base_preferences())
    assert config.model == "gpt-5"
    assert config.max_output_tokens == 500


def test_config_custom_model_requires_name() -> None:
    prefs = _base_preferences()
    prefs["model"] = "custom"
    prefs["custom_model"] = ""
    with pytest.raises(ConfigError):
        PluginConfig.from_preferences(prefs)


def test_config_custom_model_is_accepted() -> None:
    prefs = _base_preferences()
    prefs["model"] = "custom"
    prefs["custom_model"] = "my-lab-model"
    config = PluginConfig.from_preferences(prefs)
    assert config.model == "my-lab-model"


def test_config_rejects_invalid_temperature() -> None:
    prefs = _base_preferences()
    prefs["temperature"] = "3"
    with pytest.raises(ConfigError):
        PluginConfig.from_preferences(prefs)


def test_config_rejects_http_endpoint() -> None:
    prefs = _base_preferences()
    prefs["endpoint_url"] = "http://api.openai.com/v1/responses"
    with pytest.raises(ConfigError):
        PluginConfig.from_preferences(prefs)


def test_config_defaults_locale_when_invalid() -> None:
    prefs = _base_preferences()
    prefs["locale"] = "de"
    config = PluginConfig.from_preferences(prefs)
    assert config.locale == "ru"
