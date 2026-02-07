"""Configuration parsing and validation for Ulauncher preferences."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .utils import parse_bool

DEFAULT_ENDPOINT = "https://api.openai.com/v1/responses"
DEFAULT_MODEL = "gpt-5"
ALLOWED_MODELS = {"gpt-5", "gpt-5-mini", "gpt-5-nano"}
ALLOWED_VERBOSITY = {"low", "medium", "high"}
ALLOWED_REASONING = {"minimal", "low", "medium", "high"}
ALLOWED_LOCALES = {"ru", "en"}


class ConfigError(ValueError):
    """Raised when preferences cannot be parsed safely."""


@dataclass(frozen=True)
class PluginConfig:
    """Validated, normalized plugin preferences."""

    api_key: str
    endpoint_url: str
    model: str
    system_prompt: str
    temperature: float
    max_output_tokens: int
    top_p: float
    frequency_penalty: float
    presence_penalty: float
    line_wrap: int
    verbosity: str
    reasoning_effort: str
    debug_mode: bool
    locale: str

    @classmethod
    def from_preferences(cls, preferences: dict[str, Any]) -> PluginConfig:
        """Build validated config from raw Ulauncher preference map."""
        api_key = str(preferences.get("api_key", "")).strip()
        if not api_key:
            raise ConfigError("OpenAI API Key не задан")

        selected_model = str(preferences.get("model", DEFAULT_MODEL)).strip()
        custom_model = str(preferences.get("custom_model", "")).strip()
        if selected_model == "custom":
            if not custom_model:
                raise ConfigError("Custom model выбран, но поле Custom Model Name пустое")
            model = custom_model
        elif selected_model in ALLOWED_MODELS:
            model = selected_model
        else:
            raise ConfigError(
                "Недопустимая модель. Используйте gpt-5/gpt-5-mini/gpt-5-nano или custom"
            )

        endpoint_url = (
            str(preferences.get("endpoint_url", DEFAULT_ENDPOINT)).strip() or DEFAULT_ENDPOINT
        )
        if not endpoint_url.startswith("https://"):
            raise ConfigError("endpoint_url должен начинаться с https://")

        system_prompt = str(preferences.get("system_prompt", "Ты полезный ассистент")).strip()
        if not system_prompt:
            system_prompt = "Ты полезный ассистент"

        temperature = _to_float(preferences, "temperature", default=1.0, minimum=0.0, maximum=2.0)
        top_p = _to_float(preferences, "top_p", default=1.0, minimum=0.0, maximum=1.0)
        frequency_penalty = _to_float(
            preferences,
            "frequency_penalty",
            default=0.0,
            minimum=-2.0,
            maximum=2.0,
        )
        presence_penalty = _to_float(
            preferences,
            "presence_penalty",
            default=0.0,
            minimum=-2.0,
            maximum=2.0,
        )
        max_output_tokens = _to_int(
            preferences,
            key="max_completion_tokens",
            default=500,
            minimum=1,
            maximum=32_000,
        )
        line_wrap = _to_int(preferences, key="line_wrap", default=50, minimum=20, maximum=500)

        verbosity = str(preferences.get("verbosity", "low")).strip().lower()
        if verbosity not in ALLOWED_VERBOSITY:
            verbosity = "low"

        reasoning_effort = str(preferences.get("reasoning_effort", "minimal")).strip().lower()
        if reasoning_effort not in ALLOWED_REASONING:
            reasoning_effort = "minimal"

        debug_mode = parse_bool(preferences.get("debug_mode", False), default=False)

        locale = str(preferences.get("locale", "ru")).strip().lower()
        if locale not in ALLOWED_LOCALES:
            locale = "ru"

        return cls(
            api_key=api_key,
            endpoint_url=endpoint_url,
            model=model,
            system_prompt=system_prompt,
            temperature=temperature,
            max_output_tokens=max_output_tokens,
            top_p=top_p,
            frequency_penalty=frequency_penalty,
            presence_penalty=presence_penalty,
            line_wrap=line_wrap,
            verbosity=verbosity,
            reasoning_effort=reasoning_effort,
            debug_mode=debug_mode,
            locale=locale,
        )


def _to_int(
    preferences: dict[str, Any],
    key: str,
    default: int,
    minimum: int,
    maximum: int,
) -> int:
    raw = preferences.get(key, default)
    try:
        value = int(raw)
    except (TypeError, ValueError) as exc:
        raise ConfigError(f"Поле {key} должно быть числом") from exc
    if value < minimum or value > maximum:
        raise ConfigError(f"Поле {key} должно быть в диапазоне [{minimum}, {maximum}]")
    return value


def _to_float(
    preferences: dict[str, Any],
    key: str,
    default: float,
    minimum: float,
    maximum: float,
) -> float:
    raw = preferences.get(key, default)
    try:
        value = float(raw)
    except (TypeError, ValueError) as exc:
        raise ConfigError(f"Поле {key} должно быть числом") from exc
    if value < minimum or value > maximum:
        raise ConfigError(f"Поле {key} должно быть в диапазоне [{minimum}, {maximum}]")
    return value
