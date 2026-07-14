"""Тесты для дополнительных парсеров (КПП, ОГРН, БИК, р/с, и т.д.)."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from credit_check.parsers.kpp import parse_kpp
from credit_check.parsers.ogrn import parse_ogrn
from credit_check.parsers.bik import parse_bik
from credit_check.parsers.account import parse_account, parse_correspondent_account
from credit_check.parsers.email import parse_email
from credit_check.parsers.phone import parse_phone
from credit_check.parsers.doc_number import parse_doc_number
from credit_check.parsers.vat import parse_vat_rate, is_vat_exempt
from credit_check.parsers.currency import parse_currency


def test_parse_kpp_basic():
    assert parse_kpp("КПП 770101001") == "770101001"
    assert parse_kpp("КПП: 770101001") == "770101001"
    assert parse_kpp("ИНН/КПП: 7701234567 / 770101001") == "770101001"


def test_parse_kpp_none():
    assert parse_kpp("без КПП") is None
    assert parse_kpp("") is None


def test_parse_ogrn_basic():
    assert parse_ogrn("ОГРН 1234567890123") == "1234567890123"
    assert parse_ogrn("ОГРНИП 123456789012345") == "123456789012345"


def test_parse_ogrn_none():
    assert parse_ogrn("нет ОГРН") is None


def test_parse_bik_basic():
    assert parse_bik("БИК 044525225") == "044525225"
    assert parse_bik("БИК: 044525111") == "044525111"


def test_parse_bik_none():
    assert parse_bik("без БИК") is None


def test_parse_account_basic():
    assert parse_account("р/с 40702810500000012345") == "40702810500000012345"
    assert parse_correspondent_account("к/с 30101810400000000225") == "30101810400000000225"


def test_parse_account_none():
    assert parse_account("без счёта") is None


def test_parse_email_basic():
    assert parse_email("Email: info@example.com") == "info@example.com"
    assert parse_email("связь: TEST.Mail@yandex.ru") == "test.mail@yandex.ru"


def test_parse_email_none():
    assert parse_email("без email") is None


def test_parse_phone_basic():
    assert parse_phone("тел: +7 (495) 123-45-67") == "+74951234567"
    assert parse_phone("тел: 8 999 123 45 67") == "+79991234567"


def test_parse_phone_none():
    assert parse_phone("без телефона") is None


def test_parse_doc_number_basic():
    assert parse_doc_number("Договор № 47/2025") == "47/2025"
    assert parse_doc_number("Счёт №12") is not None


def test_parse_vat_rate_basic():
    assert parse_vat_rate("НДС 20%") == 20
    assert parse_vat_rate("в т.ч. НДС 10%") == 10


def test_parse_vat_exempt():
    assert is_vat_exempt("НДС не облагается (УСН)") is True
    assert is_vat_exempt("в т.ч. НДС 208 333,33 руб.") is False


def test_parse_currency_basic():
    assert parse_currency("Сумма: 1 250 000,00 руб.") == "RUB"
    assert parse_currency("$1000") == "USD"
    assert parse_currency("Стоимость 100 евро") == "EUR"
