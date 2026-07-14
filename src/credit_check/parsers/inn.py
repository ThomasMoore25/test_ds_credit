"""Парсер ИНН.

Поддерживаемые форматы:
    ИНН 7701234567         — 10-значный (юрлицо)
    ИНН 504712345678       — 12-значный (ИП)
    ИНН/КПП: 7701234567 / 770101001
    ИНН 770l234567         — OCR-мусор (буква l вместо 1) — детектируется, но не возвращается

Возвращает строку из 10 или 12 цифр либо None.
"""

from __future__ import annotations

import re
from typing import Final

# Поиск ИНН с явным префиксом «ИНН»
_INN_PATTERN: Final[re.Pattern[str]] = re.compile(
    r"ИНН\s*/?\s*КПП\s*[:]?\s*(\d[\dOoIl|]{9,11}\d)",
    re.IGNORECASE,
)
_INN_PATTERN_SIMPLE: Final[re.Pattern[str]] = re.compile(
    r"ИНН\s*[:]?\s*(\d[\dOoIl|]{9,11}\d)",
    re.IGNORECASE,
)

# Чистые 10 или 12 цифр без контекста (на случай отсутствия префикса)
_BARE_INN_PATTERN: Final[re.Pattern[str]] = re.compile(
    r"(?<!\d)(\d{10}|\d{12})(?!\d)",
)


def _is_valid_inn(s: str) -> bool:
    """True, если строка — валидный ИНН (10 или 12 цифр без посторонних символов)."""
    return bool(re.fullmatch(r"\d{10}|\d{12}", s))


def parse_inn(text: str) -> str | None:
    """Извлекает ИНН из текста.

    Возвращает строку из 10 (юрлицо) или 12 (ИП) цифр либо None.
    ИНН, распознанные в OCR-мусоре (с буквами вместо цифр), не возвращаются —
    это намеренно: для казначейства лучше вернуть None, чем рисковать неверным плательщиком.
    """
    if not text:
        return None

    # 1. ИНН с префиксом
    for pattern in (_INN_PATTERN, _INN_PATTERN_SIMPLE):
        for m in pattern.finditer(text):
            candidate = m.group(1)
            if _is_valid_inn(candidate):
                return candidate

    # 2. Bare 10/12 цифр без контекста
    for m in _BARE_INN_PATTERN.finditer(text):
        candidate = m.group(1)
        if _is_valid_inn(candidate):
            return candidate

    return None
