"""Парсер адреса — упрощённый, ищет «г. ...», «ул. ...», «д. ...»."""
from __future__ import annotations
import re
from typing import Final

_ADDRESS_PATTERN: Final[re.Pattern[str]] = re.compile(
    r"(г\.\s*[А-Яа-яЁё\-]+\s*,?\s*ул\.\s*[А-Яа-яЁё\-]+\s*,?\s*д\.\s*\d+)",
    re.IGNORECASE,
)


def parse_address(text: str) -> str | None:
    """Извлекает адрес (упрощённо — по маркерам г./ул./д.)."""
    if not text:
        return None
    m = _ADDRESS_PATTERN.search(text)
    if not m:
        return None
    addr = m.group(1).strip().rstrip(".,;")
    addr = re.sub(r"\s+", " ", addr)
    return addr if len(addr) >= 5 else None
