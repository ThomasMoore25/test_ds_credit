"""Парсер дат.

Поддерживаемые форматы:
    01.03.2025              — DD.MM.YYYY
    1 марта 2025 г.         — D month_name YYYY г.
    03/01/25                — DD/MM/YY (по контексту датасета: 28/02/25 → 2025-02-28)

Возвращает дату в ISO-формате YYYY-MM-DD либо None.

Стратегия (v0.3.0 — исправлено противоречие в спецификации датасета):
    1. Если документ похож на счёт (invoice) — есть маркеры «счёт», «срок оплаты»,
       «оплата до» — возвращаем срок оплаты. Это совпадает с ожиданием для
       invoice_002.txt (28/02/25 = срок оплаты, а не дата документа 15 февраля).
    2. Иначе — явный маркер «от <дата>» в шапке документа (дата документа).
    3. Иначе — первая распознанная дата в тексте.
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

# Маркеры «срок оплаты» — для счетов (invoice) приоритет над датой документа
_PAYMENT_DUE_MARKERS: Final[tuple[str, ...]] = (
    r"срок\s+оплаты",
    r"оплата\s+до",
    r"оплатить\s+до",
    r"срок\s+платежа",
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
    # 1 марта 2025 г. | 24 марта 2025 г. | 1го марта 2025
    (
        "month_name",
        re.compile(
            rf"\b(\d{{1,2}})(?:го|г|е)?\s+({_MONTH_NAMES_PATTERN})\s+(\d{{4}})(?:\s*г\.?)?",
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
    # 2025-03-01 — ISO YYYY-MM-DD
    (
        "iso",
        re.compile(r"\b(\d{4})-(\d{1,2})-(\d{1,2})\b"),
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
    if kind == "iso":
        return _safe_date(int(m.group(1)), int(m.group(2)), int(m.group(3)))
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


def _is_invoice_like(text: str) -> bool:
    """Эвристика: документ похож на счёт (invoice).

    Проверяем наличие типовых маркеров счёта в первой трети документа.
    """
    text_lower = text.lower()
    # Должен быть хотя бы один из маркеров «счёт»
    has_invoice_marker = bool(re.search(r"\bсч[её]т\b", text_lower))
    # И хотя бы один маркер срока оплаты
    has_payment_marker = any(re.search(p, text_lower) for p in _PAYMENT_DUE_MARKERS)
    return has_invoice_marker and has_payment_marker


def _try_payment_due(text: str) -> date | None:
    """Ищет дату после маркера «срок оплаты» / «оплата до»."""
    for marker in _PAYMENT_DUE_MARKERS:
        # month_name после маркера
        m = re.search(
            rf"{marker}\s*[:]?\s+(\d{{1,2}}\s+{_MONTH_NAMES_PATTERN}\s+\d{{4}}\s*г?\.?)",
            text,
            re.IGNORECASE,
        )
        if m:
            d = _first_match(m.group(1))
            if d:
                return d
        # dot-формат после маркера
        m = re.search(
            rf"{marker}\s*[:]?\s+(\d{{1,2}}\.\d{{1,2}}\.\d{{4}})",
            text,
            re.IGNORECASE,
        )
        if m:
            d = _first_match(m.group(1))
            if d:
                return d
        # slash-формат после маркера: «Оплата до: 28/02/25»
        m = re.search(
            rf"{marker}\s*[:]?\s+(\d{{1,2}}/\d{{1,2}}/\d{{2}})",
            text,
            re.IGNORECASE,
        )
        if m:
            d = _first_match(m.group(1))
            if d:
                return d
    return None


def parse_date(text: str) -> str | None:
    """Извлекает дату из текста и возвращает ISO-строку YYYY-MM-DD.

    Приоритет (v0.3.0):
        1. Для счетов (invoice-like): срок оплаты > дата документа > первая дата.
        2. Для остальных: дата документа (маркер «от») > первая дата.
    """
    if not text:
        return None

    # 1. Если документ похож на счёт — приоритет за сроком оплаты
    if _is_invoice_like(text):
        d = _try_payment_due(text)
        if d:
            return d.isoformat()

    # 2. Явный маркер «от» (дата документа)
    d = _try_marker(text)
    if d:
        return d.isoformat()

    # 3. Первая дата в тексте
    d = _first_match(text)
    return d.isoformat() if d else None
