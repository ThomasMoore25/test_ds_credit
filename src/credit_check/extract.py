"""extract(text: str) -> dict — извлечение полей из документа.

Извлекает:
    amount     — float, сумма документа
    date       — ISO-строка YYYY-MM-DD
    inn        — строка из 10 или 12 цифр
    contractor — строка ('ООО «...»' / 'АО «...»' / 'ИП ...')
    subject    — строка с описанием предмета

Поля, которые не удалось найти, имеют значение None.
"""

from __future__ import annotations

from typing import TypedDict

from credit_check.parsers import (
    parse_amount,
    parse_date,
    parse_inn,
    parse_contractor,
    parse_subject,
)


class ExtractResult(TypedDict):
    """Результат extract(). None для любого неотфaунденного поля."""

    amount: float | None
    date: str | None
    inn: str | None
    contractor: str | None
    subject: str | None


def extract(text: str) -> dict:
    """Извлекает ключевые поля из текста документа.

    Args:
        text: текст документа (распознанный OCR или исходный).

    Returns:
        Словарь с ключами amount, date, inn, contractor, subject.
        Не найденные поля имеют значение None.

    Examples:
        >>> extract("Сумма: 1 250 000,00 руб.")["amount"]
        1250000.0
        >>> extract("ИНН 7701234567")["inn"]
        '7701234567'
        >>> extract("без цифр")["amount"] is None
        True
    """
    if not isinstance(text, str):
        raise TypeError(f"text must be str, got {type(text).__name__}")

    if not text.strip():
        return {
            "amount": None,
            "date": None,
            "inn": None,
            "contractor": None,
            "subject": None,
        }

    return {
        "amount": parse_amount(text),
        "date": parse_date(text),
        "inn": parse_inn(text),
        "contractor": parse_contractor(text),
        "subject": parse_subject(text),
    }
