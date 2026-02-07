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
from .pricing import power_label, power_rank, pricing_label
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


def info_action(title: str, message: str, clipboard: str | None = None) -> RenderResultListAction:
    """Show informational message block."""
    payload = clipboard if clipboard is not None else message
    return RenderResultListAction(
        [
            ExtensionResultItem(
                icon=EXTENSION_ICON,
                name=title,
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
            ExtensionSmallResultItem(
                icon=EXTENSION_ICON,
                name="Показать модели API-ключа: /models",
                on_enter=CopyToClipboardAction("/models"),
            ),
        ]
    )


def models_action(
    locale: str,
    models: list[str],
    active_model: str | None = None,
) -> RenderResultListAction:
    """Render available model list returned by /v1/models."""
    _ = locale
    models_text = ", ".join(models) if models else "Список пуст"
    items = [
        ExtensionResultItem(
            icon=EXTENSION_ICON,
            name=f"Доступные модели: {len(models)} | Текущая: {active_model or 'из настроек'}",
            description=wrap_text(models_text, 80),
            on_enter=CopyToClipboardAction("\n".join(models)),
        )
    ]
    ranked_models = sorted(models, key=lambda model: (power_rank(model), model))
    for model in ranked_models[:15]:
        label = f"[active] {model}" if active_model == model else model
        items.append(
            ExtensionSmallResultItem(
                icon=EXTENSION_ICON,
                name=f"{label} | {power_label(model)} | {pricing_label(model)}",
                on_enter=CopyToClipboardAction(f"/use-model {model}"),
            )
        )
    if len(ranked_models) > 15:
        items.append(
            ExtensionSmallResultItem(
                icon=EXTENSION_ICON,
                name=f"И ещё {len(ranked_models) - 15} моделей (полный список на первой строке)",
                on_enter=DoNothingAction(),
            )
        )
    return RenderResultListAction(items)
