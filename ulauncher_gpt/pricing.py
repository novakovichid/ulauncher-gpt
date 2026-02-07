"""Static model pricing hints for UI labels.

Prices are per 1M text tokens and can change over time.
Source snapshot: OpenAI pricing page (checked 2026-02-07).
"""

from __future__ import annotations

MODEL_PRICING: dict[str, tuple[float, float]] = {
    "gpt-4.1": (2.00, 8.00),
    "gpt-4.1-mini": (0.40, 1.60),
    "gpt-4o-mini": (0.15, 0.60),
}


def pricing_label(model: str) -> str:
    """Return compact pricing label for known models."""
    normalized = model.strip().lower()
    pricing = MODEL_PRICING.get(normalized)
    if pricing is None:
        return "цена: см. pricing"
    in_price, out_price = pricing
    return f"${in_price:g}/1M in • ${out_price:g}/1M out"
