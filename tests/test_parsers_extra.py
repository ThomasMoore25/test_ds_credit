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


# --- Тесты на извлечение из реальных файлов датасета ---

DATASET = Path(__file__).resolve().parent.parent / "dataset"


def _read(name: str) -> str:
    return (DATASET / name).read_text(encoding="utf-8")


def test_kpp_from_invoice_001():
    """В invoice_001 есть «ИНН/КПП: 7701234567 / 770101001»."""
    text = _read("invoice_001.txt")
    assert parse_kpp(text) == "770101001"


def test_bik_from_invoice_001():
    """В invoice_001 есть «БИК 044525225»."""
    text = _read("invoice_001.txt")
    assert parse_bik(text) == "044525225"


def test_account_from_invoice_001():
    """В invoice_001 есть «р/с 40702810500000012345»."""
    text = _read("invoice_001.txt")
    assert parse_account(text) == "40702810500000012345"


def test_doc_number_from_contract_001():
    """В contract_001 есть «№ 47/2025»."""
    text = _read("contract_001.txt")
    n = parse_doc_number(text)
    assert n is not None
    assert "47" in n


def test_vat_rate_from_act_001():
    """В act_001 есть «НДС 20%» (в таблице)."""
    text = _read("act_001.txt")
    rate = parse_vat_rate(text)
    assert rate in (10, 20)  # зависит от того, что первым найдёт


def test_vat_exempt_from_act_002():
    """В act_002 есть «НДС не облагается (УСН)»."""
    text = _read("act_002.txt")
    assert is_vat_exempt(text) is True
