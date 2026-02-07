"""Ulauncher result item builders."""

from __future__ import annotations

from urllib.parse import quote_plus

from ulauncher.api.shared.action.CopyToClipboardAction import CopyToClipboardAction
from ulauncher.api.shared.action.DoNothingAction import DoNothingAction
from ulauncher.api.shared.action.OpenUrlAction import OpenUrlAction
from ulauncher.api.shared.action.RenderResultListAction import RenderResultListAction
from ulauncher.api.shared.item.ExtensionResultItem import ExtensionResultItem
from ulauncher.api.shared.item.ExtensionSmallResultItem import ExtensionSmallResultItem

from .i18n import t
from .utils import truncate_for_ui, wrap_text

EXTENSION_ICON = "images/icon.png"
GOOGLE_ICON = "images/google-logo.png"


def empty_prompt_action(locale: str) -> RenderResultListAction:
    """Show instruction when user has not entered a query."""
    return RenderResultListAction(
        [
            ExtensionResultItem(
                icon=EXTENSION_ICON,
                name=t(locale, "empty_prompt"),
                on_enter=DoNothingAction(),
            )
        ]
    )


def error_action(locale: str, message: str, clipboard: str | None = None) -> RenderResultListAction:
    """Show safe error block and copy details on Enter."""
    payload = clipboard if clipboard is not None else message
    return RenderResultListAction(
        [
            ExtensionResultItem(
                icon=EXTENSION_ICON,
                name=t(locale, "error_title"),
                description=wrap_text(message),
                on_enter=CopyToClipboardAction(payload),
            )
        ]
    )


def success_action(locale: str, answer: str, prompt: str, line_wrap: int) -> RenderResultListAction:
    """Render completion and convenience links for prompt."""
    ui_text = truncate_for_ui(wrap_text(answer, line_wrap))
    encoded_prompt = quote_plus(prompt)

    return RenderResultListAction(
        [
            ExtensionSmallResultItem(
                icon=EXTENSION_ICON,
                name=ui_text,
                on_enter=CopyToClipboardAction(answer),
            ),
            ExtensionSmallResultItem(
                icon=EXTENSION_ICON,
                name=t(locale, "open_chatgpt"),
                on_enter=OpenUrlAction(f"https://chatgpt.com/?prompt={encoded_prompt}"),
            ),
            ExtensionSmallResultItem(
                icon=GOOGLE_ICON,
                name=t(locale, "open_google"),
                on_enter=OpenUrlAction(f"https://www.google.com/search?q={encoded_prompt}"),
            ),
        ]
    )
