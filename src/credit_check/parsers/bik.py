"""Парсер БИК (банковский идентификационный код) — 9 цифр."""
from __future__ import annotations
import re
from typing import Final

_BIK_PATTERN: Final[re.Pattern[str]] = re.compile(
    r"БИК\s*[:]?\s*(\d{9})\b",
    re.IGNORECASE,
)


def parse_bik(text: str) -> str | None:
    """Извлекает БИК банка (9 цифр)."""
    if not text:
        return None
    m = _BIK_PATTERN.search(text)
    return m.group(1) if m else None
