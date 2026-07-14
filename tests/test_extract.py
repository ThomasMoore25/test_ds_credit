"""Тесты для extract()."""

from __future__ import annotations

from credit_check import extract


# --- Обязательные тесты из задания --------------------------------------------

def test_extract_amount_russian_format():
    """1 250 000,00 руб. → 1_250_000.0"""
    assert extract("Сумма: 1 250 000,00 руб.")["amount"] == 1_250_000.0


def test_extract_inn_simple():
    """ИНН 7701234567 → '7701234567'"""
    assert extract("ИНН 7701234567")["inn"] == "7701234567"


def test_extract_amount_none_when_no_digits():
    """без цифр → amount is None"""
    assert extract("без цифр")["amount"] is None


# --- Дополнительные кейсы по форматам -----------------------------------------

def test_extract_amount_dot_rub():
    """1250000.00 ₽ → 1250000.0"""
    assert extract("Сумма: 1250000.00 ₽")["amount"] == 1_250_000.0


def test_extract_amount_english_format():
    """1,250,000.00 RUB → 1250000.0"""
    assert extract("Всего на сумму 1,250,000.00 RUB")["amount"] == 1_250_000.0


def test_extract_amount_spellout():
    """«девятьсот тысяч рублей» → 900000.0"""
    assert extract("Стоимость услуг составляет девятьсот тысяч рублей 00/100.")["amount"] == 900_000.0


def test_extract_date_dot_format():
    """01.03.2025 → '2025-03-01'"""
    assert extract("Договор от 01.03.2025")["date"] == "2025-03-01"


def test_extract_date_month_name():
    """1 марта 2025 г. → '2025-03-01'"""
    assert extract("Договор № 1 от 1 марта 2025 г.")["date"] == "2025-03-01"


def test_extract_date_slash_short():
    """03/01/25 → '2025-01-03' (DD/MM/YY)"""
    # 03/01/25 = 3 января 2025 (DD=03, MM=01, YY=25)
    assert extract("Оплата до: 03/01/25")["date"] == "2025-01-03"


def test_extract_date_slash_ddmm_feb_28():
    """28/02/25 → '2025-02-28' (DD/MM/YY — контекст датасета)"""
    assert extract("Оплата до: 28/02/25")["date"] == "2025-02-28"


def test_extract_inn_12_digits_ip():
    """12-значный ИНН ИП."""
    assert extract("ИП Смирнов В.А., ИНН 504712345678")["inn"] == "504712345678"


def test_extract_inn_with_kpp():
    """ИНН/КПП: 7701234567 / 770101001"""
    assert extract("ИНН/КПП: 7701234567 / 770101001")["inn"] == "7701234567"


def test_extract_contractor_ooo():
    assert extract("Поставщик: ООО «ТехАгро», ИНН 7701234567")["contractor"] == "ООО «ТехАгро»"


def test_extract_contractor_ao():
    assert extract("Исполнитель: АО «АгроСнаб»")["contractor"] == "АО «АгроСнаб»"


def test_extract_contractor_ip():
    assert extract("Исполнитель: ИП Смирнов В.А.")["contractor"] == "ИП Смирнов В.А."


def test_extract_empty_string():
    result = extract("")
    assert result == {
        "amount": None,
        "date": None,
        "inn": None,
        "contractor": None,
        "subject": None,
    }


def test_extract_no_fields():
    result = extract("просто текст без полей и реквизитов")
    assert result["amount"] is None
    assert result["date"] is None
    assert result["inn"] is None
    assert result["contractor"] is None
    assert result["subject"] is None


def test_extract_subject_explicit_marker():
    text = "Предмет: поставка семян подсолнечника сорта «Командор»"
    s = extract(text)["subject"]
    assert s is not None
    assert "семян" in s.lower()


def test_extract_subject_delivery_pattern():
    text = (
        "Поставщик обязуется передать в собственность Покупателя "
        "минеральные удобрения (карбамид марки Б, ГОСТ 2081-2010), "
        "а Покупатель обязуется принять и оплатить товар."
    )
    s = extract(text)["subject"]
    assert s is not None
    assert "удобр" in s.lower()


def test_extract_returns_dict_typed():
    """Проверка типов возвращаемых значений."""
    r = extract("Договор №1 от 01.03.2025, ООО «Ромашка», ИНН 7701234567")
    assert isinstance(r, dict)
    assert set(r.keys()) == {"amount", "date", "inn", "contractor", "subject"}
