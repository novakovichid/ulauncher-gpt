"""Minimal i18n strings map for launcher messages."""

from __future__ import annotations

STRINGS = {
    "ru": {
        "empty_prompt": "Введите запрос...",
        "error_title": "Произошла ошибка",
        "open_chatgpt": "Открыть ChatGPT в браузере",
        "open_google": "Искать в Google",
    },
    "en": {
        "empty_prompt": "Type a prompt...",
        "error_title": "An error occurred",
        "open_chatgpt": "Open ChatGPT Web",
        "open_google": "Search on Google",
    },
}


def t(locale: str, key: str) -> str:
    """Return localized string with safe fallback to RU."""
    lang = STRINGS.get(locale, STRINGS["ru"])
    return lang.get(key, STRINGS["ru"].get(key, key))
