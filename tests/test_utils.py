from ulauncher_gpt.utils import encode_query, mask_secret, parse_bool, truncate_for_ui, wrap_text


def test_wrap_text_empty() -> None:
    assert wrap_text("", 10) == ""


def test_wrap_text_respects_width() -> None:
    wrapped = wrap_text("one two three four", 7)
    assert wrapped.splitlines() == ["one two", "three", "four"]


def test_wrap_text_long_word() -> None:
    assert wrap_text("supercalifragilistic", 3) == "supercalifragilistic"


def test_truncate_for_ui() -> None:
    assert truncate_for_ui("abc", 5) == "abc"
    assert truncate_for_ui("abcdef", 5).endswith("…")


def test_encode_query() -> None:
    assert encode_query("a b+c") == "a+b%2Bc"


def test_mask_secret() -> None:
    assert mask_secret("sk-123456", 4).endswith("3456")


def test_parse_bool_variants() -> None:
    assert parse_bool("true") is True
    assert parse_bool("0") is False
    assert parse_bool(None, default=True) is True
