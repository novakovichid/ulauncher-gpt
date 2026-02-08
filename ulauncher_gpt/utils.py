"""Utility helpers for formatting, logging, and URLs."""

from __future__ import annotations

import shlex
import uuid
from typing import Any
from urllib.parse import quote_plus


def wrap_text(text: str, max_width: int = 50) -> str:
    """Wrap plain text by words to fit Ulauncher UI lines."""
    if max_width < 1:
        return text
    words = text.split()
    if not words:
        return ""

    lines: list[str] = []
    current_line = ""
    for word in words:
        candidate = f"{current_line} {word}".strip()
        if len(candidate) <= max_width:
            current_line = candidate
            continue
        if current_line:
            lines.append(current_line)
        current_line = word
    if current_line:
        lines.append(current_line)
    return "\n".join(lines)


def truncate_for_ui(text: str, max_chars: int = 2200) -> str:
    """Prevent oversized UI payloads from degrading launcher performance."""
    if len(text) <= max_chars:
        return text
    return f"{text[: max_chars - 1]}…"


def encode_query(value: str) -> str:
    """URL-encode free-form query text."""
    return quote_plus(value)


def mask_secret(secret: str, keep: int = 4) -> str:
    """Mask most of a secret for safe logs."""
    if not secret:
        return ""
    if len(secret) <= keep:
        return "*" * len(secret)
    return f"{'*' * (len(secret) - keep)}{secret[-keep:]}"


def parse_bool(raw: Any, default: bool = False) -> bool:
    """Parse Ulauncher preference values into bool."""
    if isinstance(raw, bool):
        return raw
    if raw is None:
        return default
    if isinstance(raw, (int, float)):
        return bool(raw)
    normalized = str(raw).strip().lower()
    if normalized in {"1", "true", "yes", "y", "on"}:
        return True
    if normalized in {"0", "false", "no", "n", "off"}:
        return False
    return default


def new_correlation_id() -> str:
    """Return short correlation ID for request tracing in logs."""
    return uuid.uuid4().hex[:12]


def build_preview_popup_command(text: str, max_chars: int = 120_000) -> str:
    """Build shell command that opens response text in a system popup dialog."""
    safe_text = text[:max_chars]
    quoted = shlex.quote(safe_text)
    script = (
        "text=\"$1\"; "
        "if command -v zenity >/dev/null 2>&1; then "
        "tmp=$(mktemp /tmp/ulauncher-gpt-preview.XXXXXX.txt); "
        "printf '%s' \"$text\" > \"$tmp\"; "
        "zenity --text-info --title='Ulauncher GPT Preview' "
        "--width=900 --height=700 --filename=\"$tmp\"; "
        "rm -f \"$tmp\"; "
        "elif command -v kdialog >/dev/null 2>&1; then "
        "kdialog --title 'Ulauncher GPT Preview' --msgbox \"$text\"; "
        "elif command -v xmessage >/dev/null 2>&1; then "
        "xmessage -center \"$text\"; "
        "else "
        "notify-send 'Ulauncher GPT' 'No popup tool found (install zenity/kdialog/xmessage)'; "
        "fi"
    )
    return f"bash -lc {shlex.quote(script)} _ {quoted}"
