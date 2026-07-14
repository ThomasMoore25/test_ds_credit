"""Парсер НДС — ставка и сумма.

Примеры: «НДС 20%», «в т.ч. НДС 208 333,33 руб.», «НДС не облагается».
"""
from __future__ import annotations
import re
from typing import Final

_VAT_RATE_PATTERN: Final[re.Pattern[str]] = re.compile(
    r"НДС\s*(\d{1,2})\s*%",
    re.IGNORECASE,
)
_VAT_NOT_TAXED_PATTERN: Final[re.Pattern[str]] = re.compile(
    r"НДС\s*(?:не\s+облагается|без\s+НДС|освобожд)",
    re.IGNORECASE,
)


def parse_vat_rate(text: str) -> int | None:
    """Возвращает ставку НДС в процентах (10, 20, 0) или None."""
    if not text:
        return None
    m = _VAT_RATE_PATTERN.search(text)
    if m:
        return int(m.group(1))
    if _VAT_NOT_TAXED_PATTERN.search(text):
        return 0
    return None


def is_vat_exempt(text: str) -> bool:
    """True, если НДС не облагается."""
    if not text:
        return False
    return bool(_VAT_NOT_TAXED_PATTERN.search(text))
