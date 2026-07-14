"""Парсер валюты — определяет валюту суммы в документе."""
from __future__ import annotations
import re
from typing import Final

# Маппинг обозначений валют → ISO-код
_CURRENCY_PATTERNS: Final[list[tuple[str, re.Pattern[str]]]] = [
    ("RUB", re.compile(r"\b(?:руб(?:лей|ля|ль|\.|\b)|₽|RUB)\b", re.IGNORECASE)),
    ("USD", re.compile(r"\b(?:доллар(?:ов|а)?|USD|\$)\b", re.IGNORECASE)),
    ("EUR", re.compile(r"\b(?:евро|EUR|€)\b", re.IGNORECASE)),
    ("KZT", re.compile(r"\b(?:тенге|KZT|₸)\b", re.IGNORECASE)),
    ("CNY", re.compile(r"\b(?:юаней|юань|CNY|¥)\b", re.IGNORECASE)),
]


def parse_currency(text: str) -> str | None:
    """Определяет основную валюту документа → ISO-код (RUB, USD, EUR, KZT, CNY)."""
    if not text:
        return None
    for code, pattern in _CURRENCY_PATTERNS:
        if pattern.search(text):
            return code
    return None
