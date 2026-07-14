"""Парсер телефона — поддерживает российские мобильные и городские."""
from __future__ import annotations
import re
from typing import Final

# +7 (XXX) XXX-XX-XX, 8 XXX XXX XX XX, и т.п.
_PHONE_PATTERN: Final[re.Pattern[str]] = re.compile(
    r"(?:\+7|8)[\s\-()]*(\d{3})[\s\-()]*(\d{3})[\s\-()]*(\d{2})[\s\-()]*(\d{2})"
)


def parse_phone(text: str) -> str | None:
    """Извлекает телефон в формате +7XXXXXXXXXX."""
    if not text:
        return None
    m = _PHONE_PATTERN.search(text)
    if not m:
        return None
    digits = "".join(m.groups())
    return f"+7{digits}"
