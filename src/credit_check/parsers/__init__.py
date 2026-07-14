"""Парсеры для извлечения отдельных полей из текста документа."""

from credit_check.parsers.amount import parse_amount
from credit_check.parsers.date import parse_date
from credit_check.parsers.inn import parse_inn
from credit_check.parsers.contractor import parse_contractor
from credit_check.parsers.subject import parse_subject

__all__ = [
    "parse_amount",
    "parse_date",
    "parse_inn",
    "parse_contractor",
    "parse_subject",
]
