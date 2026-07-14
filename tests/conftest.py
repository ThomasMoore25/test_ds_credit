"""Общие fixtures для тестов."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

# Добавляем src в path, чтобы тесты могли импортировать credit_check без установки
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))


@pytest.fixture
def sample_contract_text() -> str:
    """Текст стандартного договора для тестов."""
    return """ДОГОВОР ПОСТАВКИ № 47/2025
от 01.03.2025

ООО «ТехАгро», ИНН 7701234567
Сумма: 1 250 000,00 руб.
"""


@pytest.fixture
def sample_invoice_text() -> str:
    """Текст счёта для тестов."""
    return """СЧЁТ НА ОПЛАТУ № 12 от 03.03.2025
Поставщик: ООО «ТехАгро», ИНН 7701234567
Срок оплаты: до 10.03.2025
"""


@pytest.fixture
def dataset_dir() -> Path:
    """Путь к папке dataset/."""
    return Path(__file__).resolve().parent.parent / "dataset"
