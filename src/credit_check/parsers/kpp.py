"""Парсер КПП (код причины постановки на учёт).

КПП — 9 цифр, обычно идёт рядом с ИНН юрлица.
Формат: «КПП 770101001» / «КПП: 770101001» / «ИНН/КПП: 7701234567 / 770101001».
"""
from __future__ import annotations
import re
from typing import Final

_KPP_PATTERN: Final[re.Pattern[str]] = re.compile(
    r"КПП\s*[:]?\s*(\d{9})\b",
    re.IGNORECASE,
)


def parse_kpp(text: str) -> str | None:
    """Извлекает КПП (9 цифр) из текста."""
    if not text:
        return None
    m = _KPP_PATTERN.search(text)
    return m.group(1) if m else None
