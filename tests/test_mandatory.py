"""Обязательные assert'ы из тестового задания — все в одном файле.

Задание:
    assert extract("Сумма: 1 250 000,00 руб.")["amount"] == 1_250_000.0
    assert extract("ИНН 7701234567")["inn"] == "7701234567"
    assert extract("без цифр")["amount"] is None

    doc_type, confidence = classify("Счёт на оплату №12 от 01.03.2025 ...")
    assert doc_type == "invoice"
    assert confidence > 0.5
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from credit_check import classify, extract


def test_mandatory_extract_amount():
    """Обязательный assert #1: extract('Сумма: 1 250 000,00 руб.')['amount'] == 1_250_000.0"""
    assert extract("Сумма: 1 250 000,00 руб.")["amount"] == 1_250_000.0


def test_mandatory_extract_inn():
    """Обязательный assert #2: extract('ИНН 7701234567')['inn'] == '7701234567'"""
    assert extract("ИНН 7701234567")["inn"] == "7701234567"


def test_mandatory_extract_no_digits():
    """Обязательный assert #3: extract('без цифр')['amount'] is None"""
    assert extract("без цифр")["amount"] is None


def test_mandatory_classify_invoice():
    """Обязательный assert #4: classify('Счёт на оплату №12 от 01.03.2025 ...') == invoice, > 0.5"""
    doc_type, confidence = classify("Счёт на оплату №12 от 01.03.2025 ...")
    assert doc_type == "invoice"
    assert confidence > 0.5
