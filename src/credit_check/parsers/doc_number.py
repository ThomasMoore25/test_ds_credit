"""Парсер номера документа — «№ 47/2025», «№12», «№ 38»."""
from __future__ import annotations
import re
from typing import Final

_DOC_NUMBER_PATTERN: Final[re.Pattern[str]] = re.compile(
    r"№\s*([A-Za-zА-Яа-я]?\d+[\-/\.]\d+|\d+[A-Za-zА-Яа-я]?[\/\-\.]?\d*)",
    re.IGNORECASE,
)


def parse_doc_number(text: str) -> str | None:
    """Извлекает номер документа после «№»."""
    if not text:
        return None
    m = _DOC_NUMBER_PATTERN.search(text)
    return m.group(1).strip() if m else None
