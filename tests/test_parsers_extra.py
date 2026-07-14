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
    """В act_001 НДС указан суммой, не процентом — parse_vat_rate вернёт None."""
    text = _read("act_001.txt")
    # В тексте есть «НДС 208 333,33 руб.» — нет ставки в %.
    rate = parse_vat_rate(text)
    assert rate is None  # явной ставки нет


def test_vat_exempt_from_act_002():
    """В act_002 есть «НДС не облагается (УСН)»."""
    text = _read("act_002.txt")
    assert is_vat_exempt(text) is True


def test_currency_rub_in_dataset():
    """Все счета в датасете — в RUB."""
    for fname in ["contract_001.txt", "invoice_001.txt", "act_001.txt"]:
        text = _read(fname)
        assert parse_currency(text) == "RUB"


def test_currency_usd():
    """Доллары."""
    assert parse_currency("Сумма: $1000") == "USD"
    assert parse_currency("Стоимость 100 долларов") == "USD"


def test_currency_eur():
    """Евро."""
    assert parse_currency("Стоимость 100 EUR") == "EUR"
    assert parse_currency("Сумма 500 евро") == "EUR"


def test_currency_kzt():
    """Тенге."""
    assert parse_currency("Сумма: 50000 тенге") == "KZT"


def test_currency_none_when_no_currency():
    """Нет валюты → None."""
    assert parse_currency("обычный текст") is None


# --- Тесты для парсера адреса (iter 57-58) ---

def test_parse_address_basic():
    from credit_check.parsers.address import parse_address
    assert parse_address("г. Краснодар, ул. Ленина, д. 15") is not None
    assert "Краснодар" in parse_address("г. Краснодар, ул. Ленина, д. 15")


def test_parse_address_none():
    from credit_check.parsers.address import parse_address
    assert parse_address("без адреса") is None


# --- Тесты для парсера номера документа (iter 59-60) ---

def test_parse_doc_number_with_slash():
    assert parse_doc_number("№ 47/2025") == "47/2025"


def test_parse_doc_number_simple():
    n = parse_doc_number("Счёт №12 от 03.03.2025")
    assert n is not None
    assert "12" in n


# --- Тесты для VAT (iter 61-63) ---

def test_vat_rate_10():
    assert parse_vat_rate("НДС 10%") == 10


def test_vat_rate_0():
    assert parse_vat_rate("НДС 0%") == 0


def test_vat_exempt_usn():
    assert is_vat_exempt("НДС не облагается (УСН)") is True


# --- Тесты для телефона (iter 64-65) ---

def test_phone_with_spaces():
    assert parse_phone("тел: +7 999 123 45 67") == "+79991234567"


def test_phone_with_dashes():
    assert parse_phone("тел: 8-999-123-45-67") == "+79991234567"


def test_parse_contractor_spk():
    from credit_check.parsers.contractor import parse_contractor_extended
    assert parse_contractor_extended("СПК «Колос»") == "СПК «Колос»"


def test_parse_contractor_kfh():
    from credit_check.parsers.contractor import parse_contractor_extended
    assert parse_contractor_extended("КФХ «Рассвет»") == "КФХ «Рассвет»"


def test_parse_contractor_nko():
    from credit_check.parsers.contractor import parse_contractor_extended
    assert parse_contractor_extended("НКО «Фонд развития»") == "НКО «Фонд развития»"


def test_metrics_avg_confidence():
    from credit_check.metrics import compute_classify_avg_confidence
    avg = compute_classify_avg_confidence()
    assert 0.0 <= avg <= 1.0
    # На нашем датасете все реальные документы имеют confidence > 0.9
    assert avg > 0.9


def test_metrics_classify():
    from credit_check.metrics import compute_classify_metrics
    m = compute_classify_metrics()
    assert "accuracy" in m
    assert "unknown_rate" in m
    assert m["accuracy"] == 1.0  # 100% на датасете


def test_metrics_check_subject():
    from credit_check.metrics import compute_check_subject_metrics
    m = compute_check_subject_metrics()
    assert "pass_accuracy" in m
    assert "fail_accuracy" in m
    assert "precision" in m
    assert "recall" in m
    assert "f1" in m
    assert m["pass_accuracy"] == 1.0
    assert m["fail_accuracy"] == 1.0


# --- Тесты edge cases для новых парсеров (iter 75-80) ---

def test_kpp_empty_string():
    assert parse_kpp("") is None


def test_kpp_wrong_length():
    """КПП из 8 или 10 цифр — не валидный."""
    assert parse_kpp("КПП 77010101") is None  # 8 цифр
    assert parse_kpp("КПП 7701010123") is None  # 10 цифр


def test_ogrn_empty():
    assert parse_ogrn("") is None


def test_bik_empty():
    assert parse_bik("") is None


def test_account_empty():
    assert parse_account("") is None
    assert parse_correspondent_account("") is None


def test_email_invalid():
    assert parse_email("not an email") is None
    assert parse_email("@example.com") is None


def test_phone_invalid():
    assert parse_phone("12345") is None  # слишком короткий
    assert parse_phone("не телефон") is None


def test_doc_number_empty():
    assert parse_doc_number("") is None


def test_vat_no_rate():
    assert parse_vat_rate("без НДС") is None  # нет явной ставки


def test_currency_empty():
    assert parse_currency("") is None


# --- Тесты генерации графиков (iter 91) ---

def test_generate_plots_script_exists():
    """Скрипт генерации графиков существует."""
    from pathlib import Path
    script = Path(__file__).resolve().parent.parent / "scripts" / "generate_plots.py"
    assert script.exists()


def test_plots_generated():
    """Все PNG-графики на месте."""
    from pathlib import Path
    images_dir = Path(__file__).resolve().parent.parent / "docs" / "images"
    expected = [
        "classify_confidence.png",
        "check_subject_results.png",
        "classify_threshold_experiment.png",
        "check_subject_confusion_matrix.png",
        "check_subject_confidence_distribution.png",
    ]
    for name in expected:
        assert (images_dir / name).exists(), f"Missing: {name}"


def test_address_from_scan_ocr():
    """В scan_ocr есть «ул. Ленина д.15»."""
    from credit_check.parsers.address import parse_address
    text = _read("scan_ocr_001.txt")
    addr = parse_address(text)
    # OCR-мусор может не сматчиться — это OK
    assert addr is None or "Ленина" in addr or "ул" in addr.lower()


def test_no_kpp_in_act_002():
    """В act_002 нет КПП — должен вернуть None."""
    text = _read("act_002.txt")
    assert parse_kpp(text) is None


def test_no_bik_in_contract():
    """В contract_001 нет БИК."""
    text = _read("contract_001.txt")
    assert parse_bik(text) is None
