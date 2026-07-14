"""Парсер дат.

Поддерживаемые форматы:
    01.03.2025              — DD.MM.YYYY
    1 марта 2025 г.         — D month_name YYYY г.
    03/01/25                — DD/MM/YY (по контексту датасета: 28/02/25 → 2025-02-28)

Возвращает дату в ISO-формате YYYY-MM-DD либо None.

Стратегия:
    1. Явный маркер «от <дата>» в шапке документа (приоритет) — это дата документа.
    2. Иначе — первая распознанная дата в тексте.
"""

from __future__ import annotations

import re
from datetime import date
from typing import Final

# Месяцы в русском языке (именительный + родительный падежи — обе формы встречаются).
_MONTHS_RU: Final[dict[str, int]] = {
    "января": 1, "январь": 1, "янв": 1,
    "февраля": 2, "февраль": 2, "фев": 2,
    "марта": 3, "март": 3, "мар": 3,
    "апреля": 4, "апрель": 4, "апр": 4,
    "мая": 5, "май": 5,
    "июня": 6, "июнь": 6, "июн": 6,
    "июля": 7, "июль": 7, "июл": 7,
    "августа": 8, "август": 8, "авг": 8,
    "сентября": 9, "сентябрь": 9, "сен": 9,
    "октября": 10, "октябрь": 10, "окт": 10,
    "ноября": 11, "ноябрь": 11, "ноя": 11,
    "декабря": 12, "декабрь": 12, "дек": 12,
}

_MONTH_NAMES_PATTERN: Final[str] = (
    r"(?:января|февраля|марта|апреля|мая|июня|июля|августа|"
    r"сентября|октября|ноября|декабря|"
    r"январь|февраль|март|апрель|май|июнь|июль|август|"
    r"сентябрь|октябрь|ноябрь|декабрь)"
)


def _safe_date(year: int, month: int, day: int) -> date | None:
    """Создаёт date с защитой от невалидных комбинаций."""
    try:
        return date(year, month, day)
    except (ValueError, OverflowError):
        return None


def _expand_2digit_year(yy: int) -> int:
    """Расширяет 2-значный год до 4-значного (порог 50: 25→2025, 75→1975)."""
    return 2000 + yy if yy < 50 else 1900 + yy


# --- Шаблоны дат (применяются по очереди, возвращается первый match) ----------

_DATE_PATTERNS: Final[list[tuple[str, re.Pattern[str]]]] = [
    # 1 марта 2025 г. | 24 марта 2025 г.
    (
        "month_name",
        re.compile(
            rf"\b(\d{{1,2}})\s+({_MONTH_NAMES_PATTERN})\s+(\d{{4}})\s*г\.?",
            re.IGNORECASE,
        ),
    ),
    # 01.03.2025 | 1.3.2025  (DD.MM.YYYY)
    (
        "dot",
        re.compile(r"\b(\d{1,2})\.(\d{1,2})\.(\d{4})\b"),
    ),
    # 03/01/25 | 28/02/25  — DD/MM/YY (по контексту датасета)
    (
        "slash_short",
        re.compile(r"\b(\d{1,2})/(\d{1,2})/(\d{2})\b"),
    ),
    # 01.03.25 — DD.MM.YY (на всякий случай)
    (
        "dot_short",
        re.compile(r"\b(\d{1,2})\.(\d{1,2})\.(\d{2})\b"),
    ),
]


def _try_pattern(text: str, kind: str, m: re.Match[str]) -> date | None:
    """Преобразует match в date в зависимости от типа паттерна."""
    if kind == "month_name":
        day = int(m.group(1))
        month = _MONTHS_RU.get(m.group(2).lower())
        year = int(m.group(3))
        if month is None:
            return None
        return _safe_date(year, month, day)
    if kind == "dot":
        return _safe_date(int(m.group(3)), int(m.group(2)), int(m.group(1)))
    if kind == "slash_short":
        return _safe_date(
            _expand_2digit_year(int(m.group(3))),
            int(m.group(2)),
            int(m.group(1)),
        )
    if kind == "dot_short":
        return _safe_date(
            _expand_2digit_year(int(m.group(3))),
            int(m.group(2)),
            int(m.group(1)),
        )
    return None


def _first_match(text: str) -> date | None:
    """Возвращает первую дату из первого совпавшего шаблона."""
    for kind, pattern in _DATE_PATTERNS:
        m = pattern.search(text)
        if not m:
            continue
        d = _try_pattern(text, kind, m)
        if d is not None:
            return d
    return None


def _try_marker(text: str) -> date | None:
    """Ищет дату после явного маркера «от» / «№ ... от»."""
    # Сначала — month_name после «от»: «№ 7 от 15 февраля 2025 г.»
    m = re.search(
        rf"(?:№\s*\S+\s+от|\bот)\s+(\d{{1,2}}\s+{_MONTH_NAMES_PATTERN}\s+\d{{4}}\s*г?\.?)",
        text,
        re.IGNORECASE,
    )
    if m:
        d = _first_match(m.group(1))
        if d:
            return d
    # Затем — dot-формат после «от»: «№ 12 от 03.03.2025»
    m = re.search(
        r"(?:№\s*\S+\s+от|\bот)\s+(\d{1,2}\.\d{1,2}\.\d{4})",
        text,
    )
    if m:
        d = _first_match(m.group(1))
        if d:
            return d
    return None


def parse_date(text: str) -> str | None:
    """Извлекает дату из текста и возвращает ISO-строку YYYY-MM-DD.

    Приоритет: явный маркер «от <дата>» в шапке документа; иначе первая дата в тексте.
    """
    if not text:
        return None

    # 1. Явный маркер «от»
    d = _try_marker(text)
    if d:
        return d.isoformat()

    # 2. Первая дата в тексте
    d = _first_match(text)
    return d.isoformat() if d else None
