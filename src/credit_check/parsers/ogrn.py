"""Парсер ОГРН (основной государственный регистрационный номер).

ОГРН — 13 цифр (юрлица) или 15 цифр (ИП, тогда ОГРНИП).
"""
from __future__ import annotations
import re
from typing import Final

_OGRN_PATTERN: Final[re.Pattern[str]] = re.compile(
    r"ОГРН(?:ИП)?\s*[:]?\s*(\d{13}|\d{15})\b",
    re.IGNORECASE,
)


def parse_ogrn(text: str) -> str | None:
    """Извлекает ОГРН (13) или ОГРНИП (15) из текста."""
    if not text:
        return None
    m = _OGRN_PATTERN.search(text)
    return m.group(1) if m else None
