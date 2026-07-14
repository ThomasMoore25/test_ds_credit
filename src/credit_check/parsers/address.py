"""Парсер адреса — упрощённый, ищет «г. ...», «ул. ...», «д. ...»."""
from __future__ import annotations
import re
from typing import Final

_ADDRESS_PATTERN: Final[re.Pattern[str]] = re.compile(
    r"((?:г\.\s*|г\s+|ул\.\s*|ул\s+|д\.\s*|д\s+|обл\.\s*|обл\s+|р-н\s+|пер\.\s*|пер\s+|пр-т\s+|наб\.\s*)"
    r"[А-Яа-яЁё\s\.,\-0-9/]{5,200}?(?=\s*(?:ИНН|КПП|ОГРН|БИК|р/с|к/с|тел|факс|email|@|$|\n))",
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
