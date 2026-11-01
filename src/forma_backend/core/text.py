"""Shared Unicode boundary validation; no transport or persistence dependencies."""


def valid_text(value: str) -> str:
    if "\x00" in value:
        raise ValueError("NUL is not allowed")
    try:
        value.encode("utf-8")
    except UnicodeEncodeError:
        raise ValueError("Invalid Unicode") from None
    return value
