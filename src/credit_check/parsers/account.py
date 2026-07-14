"""Парсер расчётного счёта (р/с) — 20 цифр."""
from __future__ import annotations
import re
from typing import Final

_RS_PATTERN: Final[re.Pattern[str]] = re.compile(
    r"\bр/с\s*[:]?\s*(\d{20})\b",
    re.IGNORECASE,
)
_KS_PATTERN: Final[re.Pattern[str]] = re.compile(
    r"\bк/с\s*[:]?\s*(\d{20})\b",
    re.IGNORECASE,
)


def parse_account(text: str) -> str | None:
    """Извлекает расчётный счёт (20 цифр)."""
    if not text:
        return None
    m = _RS_PATTERN.search(text)
    return m.group(1) if m else None


def parse_correspondent_account(text: str) -> str | None:
    """Извлекает корреспондентский счёт (к/с, 20 цифр)."""
    if not text:
        return None
    m = _KS_PATTERN.search(text)
    return m.group(1) if m else None
