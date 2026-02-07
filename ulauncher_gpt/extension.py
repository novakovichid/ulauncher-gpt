"""Ulauncher entry integration and event handling."""

from __future__ import annotations

import logging
from typing import Any

import requests
from ulauncher.api.client.EventListener import EventListener
from ulauncher.api.client.Extension import Extension
from ulauncher.api.shared.event import KeywordQueryEvent

from .config import ConfigError, PluginConfig
from .openai_client import APIError, OpenAIResponsesClient
from .presenters import empty_prompt_action, error_action, success_action
from .utils import mask_secret, new_correlation_id

logger = logging.getLogger(__name__)


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

        try:
            generated = self.client.generate(
                prompt=search_term,
                config=config,
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
            prompt=search_term,
            line_wrap=config.line_wrap,
        )
