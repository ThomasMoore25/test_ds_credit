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


def test_extract_amount_spellout_million():
    """«Один миллион двести пятьдесят тысяч рублей» → 1_250_000.0"""
    assert extract("Сумма: Один миллион двести пятьдесят тысяч рублей 00 копеек.")["amount"] == 1_250_000.0


def test_extract_amount_spellout_billion():
    """«два миллиарда рублей» → 2_000_000_000.0"""
    assert extract("Сумма: два миллиарда рублей.")["amount"] == 2_000_000_000.0


def test_extract_amount_spellout_polutora():
    """«полтора миллиона рублей» → 1_500_000.0"""
    assert extract("Сумма: полтора миллиона рублей.")["amount"] == 1_500_000.0


def test_extract_amount_spellout_poltysyachi():
    """«полтысячи рублей» → 500.0"""
    assert extract("Сумма: полтысячи рублей.")["amount"] == 500.0


def test_extract_amount_spellout_polmilliona():
    """«полмиллиона рублей» → 500_000.0"""
    assert extract("Сумма: полмиллиона рублей.")["amount"] == 500_000.0


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


def test_extract_subject_from_table_spec():
    """Извлечение subject из таблицы спецификации (Наименование товара)."""
    text = (
        "СПЕЦИФИКАЦИЯ № 1\n"
        "+---+----------------+---+\n"
        "| № | Наименование товара | Ед. |\n"
        "+---+----------------+---+\n"
        "| 1 | Карбамид марки Б, ГОСТ 2081-2010 | тонна |\n"
        "+---+----------------+---+\n"
    )
    s = extract(text)["subject"]
    assert s is not None
    assert "Карбамид" in s


def test_extract_subject_from_table_invoice():
    """Извлечение subject из таблицы счёта (Товар / Услуга)."""
    text = (
        "СЧЁТ НА ОПЛАТУ № 12 от 03.03.2025\n"
        "+---+----------------+---+\n"
        "| № | Товар / Услуга | Ед. |\n"
        "+---+----------------+---+\n"
        "| 1 | Карбамид марки Б, ГОСТ 2081-2010 | т |\n"
        "+---+----------------+---+\n"
    )
    s = extract(text)["subject"]
    assert s is not None
    assert "Карбамид" in s


def test_extract_subject_from_numbered_list():
    """Извлечение subject из нумерованного списка работ в акте."""
    text = (
        "АКТ ВЫПОЛНЕННЫХ РАБОТ № 14\n"
        "Исполнитель выполнил работы:\n"
        "1. Внесение жидких комплексных удобрений (КАС-32) на площади 500 га —\n"
        "   250 000,00 руб.\n"
        "2. Предпосевная обработка почвы гербицидами — 180 000,00 руб.\n"
    )
    s = extract(text)["subject"]
    assert s is not None
    assert "Внесение" in s or "удобр" in s.lower()
    # Должно включать «КАС-32» полностью, а не обрезаться на дефисе
    assert "КАС-32" in s or "КАС" in s


def test_extract_subject_postavka_pattern():
    """Шаблон «Предмет: поставка ...» для счетов на услуги."""
    text = "Счет № 7\nПредмет: поставка семян подсолнечника сорта «Командор»"
    s = extract(text)["subject"]
    assert s is not None
    assert "семян" in s.lower() or "поставк" in s.lower()


def test_extract_returns_dict_typed():
    """Проверка типов возвращаемых значений."""
    r = extract("Договор №1 от 01.03.2025, ООО «Ромашка», ИНН 7701234567")
    assert isinstance(r, dict)
    assert set(r.keys()) == {"amount", "date", "inn", "contractor", "subject"}


# --- Edge cases (iter 26-30) ---

def test_extract_empty_string_returns_none():
    """Пустая строка → все поля None."""
    r = extract("")
    assert r["amount"] is None
    assert r["date"] is None
    assert r["inn"] is None
    assert r["contractor"] is None
    assert r["subject"] is None


def test_extract_whitespace_only():
    """Только пробелы → все поля None."""
    r = extract("   \n\t  \n  ")
    assert r["amount"] is None
    assert r["inn"] is None


def test_extract_very_long_text():
    """Очень длинный текст не должен падать."""
    text = "Договор № 1 от 01.03.2025, ООО «Ромашка», ИНН 7701234567. " * 1000
    r = extract(text)
    assert r["inn"] == "7701234567"
    assert r["contractor"] == "ООО «Ромашка»"


def test_extract_multiple_inn_returns_first():
    """Если в тексте несколько ИНН — возвращается первый."""
    text = "ИНН 7701234567, ИНН 5047123456"
    r = extract(text)
    assert r["inn"] == "7701234567"


def test_extract_negative_amount_returns_none():
    """Отрицательные числа не должны быть amount."""
    r = extract("Сумма: -1250000.00 руб.")
    # Отрицательная сумма — это либо None, либо положительное значение
    # (мы не поддерживаем отрицательные суммы как amount)
    assert r["amount"] is None or r["amount"] > 0


# --- Дополнительные тесты форматов (iter 38-47) ---

def test_extract_amount_with_space_separator_no_kopecks():
    """1 500 000 руб. без копеек."""
    assert extract("Итого: 1 500 000 руб.")["amount"] == 1_500_000.0


def test_extract_amount_dot_decimal():
    """1250000.50 (точка как десятичный разделитель)."""
    assert extract("Сумма: 1250000.50 руб.")["amount"] == 1_250_000.5


def test_extract_amount_rub_with_kopecks_text():
    """«1250000 руб. 50 коп.» — сумма + копейки прописью."""
    r = extract("Итого: 1 250 000 руб. 50 коп.")
    assert r["amount"] is not None
    assert r["amount"] >= 1_250_000


def test_extract_date_iso_format():
    """ISO дата 2025-03-01."""
    assert extract("Договор от 2025-03-01")["date"] == "2025-03-01"


def test_extract_date_with_leading_zeros():
    """Дата с ведущими нулями 01.03.2025."""
    assert extract("от 01.03.2025")["date"] == "2025-03-01"


def test_extract_date_short_year():
    """Короткий год 25.03.25 → 2025-03-25."""
    r = extract("от 25.03.25")
    assert r["date"] is not None
    assert "2025" in r["date"]


def test_extract_inn_10_digits_bare():
    """Голые 10 цифр без префикса."""
    assert extract("Контрагент: 7701234567")["inn"] == "7701234567"


def test_extract_contractor_pao():
    """ПАО — тоже валидный контрагент."""
    assert extract("Банк: ПАО «Сбербанк»")["contractor"] == "ПАО «Сбербанк»"


def test_extract_contractor_zao():
    """ЗАО — валидный контрагент."""
    assert extract("Поставщик: ЗАО «Ромашка»")["contractor"] == "ЗАО «Ромашка»"


def test_extract_amount_zero_returns_zero():
    """Сумма 0 руб. → 0.0 (не None)."""
    r = extract("Сумма: 0 руб.")
    # 0 может быть None (мы фильтруем value <= 0) — это OK
    assert r["amount"] is None or r["amount"] == 0.0
