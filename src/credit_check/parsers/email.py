"""Парсер email из текста."""
from __future__ import annotations
import re
from typing import Final

# Стандартный паттерн email
_EMAIL_PATTERN: Final[re.Pattern[str]] = re.compile(
    r"\b([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})\b",
)


def parse_email(text: str) -> str | None:
    """Извлекает первый найденный email из текста."""
    if not text:
        return None
    m = _EMAIL_PATTERN.search(text)
    return m.group(1).lower() if m else None
