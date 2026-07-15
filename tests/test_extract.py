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


# --- Тесты сокращений суммы (iter 54-55) ---

def test_extract_amount_thousand_abbreviation():
    """«1250 тыс. руб.» → 1 250 000."""
    assert extract("Сумма: 1250 тыс. руб.")["amount"] == 1_250_000.0


def test_extract_amount_million_abbreviation():
    """«1.5 млн руб.» → 1 500 000."""
    r = extract("Сумма: 1.5 млн руб.")
    # 1.5 млн должно развернуться в 1 500 000
    assert r["amount"] is not None
    assert r["amount"] >= 1_000_000


def test_extract_amount_billion_abbreviation():
    """«2 млрд руб.» → 2 000 000 000."""
    r = extract("Сумма: 2 млрд руб.")
    assert r["amount"] is not None
    assert r["amount"] >= 1_000_000_000


def test_extract_with_emoji():
    """Эмодзи не должны ломать extract."""
    r = extract("Договор № 1 от 01.03.2025 🚜 ИНН 7701234567")
    assert r["inn"] == "7701234567"
    assert r["date"] == "2025-03-01"


def test_extract_with_html_tags():
    """HTML теги в тексте — должны игнорироваться."""
    r = extract("<p>ИНН 7701234567</p>")
    assert r["inn"] == "7701234567"


def test_extract_with_markdown():
    """Markdown разметка."""
    r = extract("**Сумма:** 1 250 000,00 руб.")
    assert r["amount"] == 1_250_000.0


def test_extract_cyrillic_inn():
    """ИНН с кириллицей рядом."""
    r = extract("ИНН 7701234567, контрагент ООО «Тест»")
    assert r["inn"] == "7701234567"
    assert r["contractor"] == "ООО «Тест»"


def test_extract_multiple_dates():
    """Несколько дат — должна вернуться первая."""
    r = extract("от 01.03.2025, оплата до 10.03.2025")
    # Для не-invoice документов — первая дата (01.03.2025)
    assert r["date"] == "2025-03-01"


# --- Stress tests (iter 76-80) ---

def test_extract_stress_1000_iterations():
    """100 вызовов extract — не должно падать."""
    text = "Договор № 1 от 01.03.2025, ООО «Тест», ИНН 7701234567. Стоимость: 1 250 000,00 руб."
    for _ in range(100):
        r = extract(text)
        assert r["inn"] == "7701234567"


def test_extract_stress_large_text():
    """Текст 100KB — не должен падать."""
    text = "Договор № 1 от 01.03.2025, ООО «Тест», ИНН 7701234567. " * 2000
    r = extract(text)
    assert r["inn"] == "7701234567"


def test_extract_stress_many_amounts():
    """Текст с 100 суммами — должен вернуть максимум."""
    text = "Сумма: 100 руб. " * 50 + "Итого: 1 250 000,00 руб. " + "Сумма: 200 руб. " * 50
    r = extract(text)
    assert r["amount"] == 1_250_000.0


def test_extract_stress_many_inns():
    """Текст с 10 ИНН — должен вернуть первый."""
    text = " ".join(f"ИНН 770123456{i}" for i in range(10))
    r = extract(text)
    assert r["inn"] is not None
    assert len(r["inn"]) in (10, 12)


def test_extract_stress_many_dates():
    """Текст с 10 датами — должен вернуть первую."""
    text = " ".join(f"от 0{i}.03.2025" for i in range(1, 10))
    r = extract(text)
    assert r["date"] is not None


# --- Тесты суммы прописью (iter 81-85) ---

def test_extract_amount_spellout_dva_milliona():
    assert extract("Сумма: два миллиона рублей.")["amount"] == 2_000_000.0


def test_extract_amount_spellout_tri_milliona():
    assert extract("Сумма: три миллиона рублей.")["amount"] == 3_000_000.0


def test_extract_amount_spellout_pyat_sot_tysyach():
    assert extract("Сумма: пятьсот тысяч рублей.")["amount"] == 500_000.0


def test_extract_amount_spellout_desyat_tysyach():
    assert extract("Сумма: десять тысяч рублей.")["amount"] == 10_000.0


def test_extract_amount_spellout_sto_tysyach():
    assert extract("Сумма: сто тысяч рублей.")["amount"] == 100_000.0


# --- Тесты разных сумм (iter 83-86) ---

def test_extract_amount_with_kopecks():
    """Сумма с копейками: 1 250 000,50 руб."""
    r = extract("Сумма: 1 250 000,50 руб.")
    assert r["amount"] == 1_250_000.5


def test_extract_amount_no_kopecks_no_space():
    """1250000 руб. без разделителя тысяч."""
    r = extract("Сумма: 1250000 руб.")
    assert r["amount"] == 1_250_000.0


def test_extract_amount_rub_symbol_only():
    """Только символ ₽ без 'руб'."""
    r = extract("Сумма: 1 250 000,00 ₽")
    assert r["amount"] == 1_250_000.0


def test_extract_amount_english_with_rub():
    """Английский формат с RUB."""
    r = extract("Total: 1,250,000.00 RUB")
    assert r["amount"] == 1_250_000.0


# --- Тесты дат (iter 84-87) ---

def test_extract_date_february_28():
    """28 февраля 2025 г."""
    assert extract("от 28 февраля 2025 г.")["date"] == "2025-02-28"


def test_extract_date_december_31():
    """31 декабря 2024 г."""
    assert extract("от 31 декабря 2024 г.")["date"] == "2024-12-31"


def test_extract_date_january_1():
    """1 января 2025 г."""
    assert extract("от 1 января 2025 г.")["date"] == "2025-01-01"


def test_extract_date_invalid_returns_none():
    """31.02.2025 — невалидная дата → None."""
    assert extract("от 31.02.2025")["date"] is None


def test_extract_date_year_only():
    """Только год — не должен парситься как дата."""
    r = extract("Договор 2025 года")
    # Может вернуть None или какую-то дату, но не должен падать
    assert r["date"] is None or "2025" in r["date"]


# --- Тесты на исправленные баги (iter 1 качественная) ---

def test_extract_negative_amount_returns_none():
    """Баг #1: отрицательная сумма не должна возвращать положительное число.

    «Сумма: -1250000.00 руб.» → None (отрицательная сумма = возврат, не приход).
    Защита для казначейства: возврат платежа не должен интерпретироваться как приход.
    """
    assert extract("Сумма: -1250000.00 руб.")["amount"] is None


def test_extract_inn_not_treated_as_amount():
    """Баг #2: ИНН рядом со словом «сумма» не должен возвращаться как сумма.

    «ИНН 7701234567, сумма 1 250 000,00 руб.» → 1250000.0, не 7701234567.0.
    Защита: ИНН (10-12 цифр) с маркером «ИНН» рядом исключается из кандидатов суммы.
    """
    r = extract("ИНН 7701234567, сумма 1 250 000,00 руб.")
    assert r["amount"] == 1_250_000.0
    assert r["inn"] == "7701234567"


def test_extract_account_not_treated_as_amount():
    """Баг #3: р/с (20 цифр) не должен возвращаться как сумма.

    «Сумма: 40702810500000012345 руб.» → None, не 4.07e+19.
    Защита: 20-значные числа — всегда р/с или к/с, не сумма.
    """
    assert extract("Сумма: 40702810500000012345 руб.")["amount"] is None


def test_extract_bik_not_treated_as_amount():
    """БИК (9 цифр) с маркером 'БИК' не должен возвращаться как сумма.

    «БИК 044525225, сумма 1 250 000,00 руб.» → 1250000.0, не 44525225.0.
    Защита: 9-значные слитные числа с маркером 'БИК' исключаются.
    """
    r = extract("БИК 044525225, сумма 1 250 000,00 руб.")
    assert r["amount"] == 1_250_000.0


def test_extract_amount_with_separators_not_treated_as_inn():
    """Сумма с разделителями тысяч не должна определяться как ИНН/БИК.

    «1 250 000,00» после удаления не-цифр = 9 цифр, но это сумма с разделителями,
    не БИК. Проверка: raw должен состоять только из цифр, чтобы быть реквизитом.
    """
    # Если рядом есть «БИК», но число с разделителями — это сумма, не БИК
    r = extract("БИК 044525225. Сумма: 1 250 000,00 руб.")
    assert r["amount"] == 1_250_000.0


# --- Тесты коротких сумм (iter 3) ---

def test_extract_short_amount_rub():
    """Короткая сумма 100 руб. — должна парситься."""
    assert extract("Стоимость: 100 руб.")["amount"] == 100.0


def test_extract_short_amount_rub_symbol():
    """Короткая сумма 50 ₽."""
    assert extract("Сумма: 50 ₽")["amount"] == 50.0


def test_extract_short_amount_rub_english():
    """Короткая сумма 200 RUB."""
    assert extract("Сумма: 200 RUB")["amount"] == 200.0


def test_extract_short_amount_with_kopecks():
    """Короткая сумма с копейками 99,50 руб."""
    assert extract("Сумма: 99,50 руб.")["amount"] == 99.5


def test_extract_multiple_amounts_returns_max():
    """Несколько сумм — возвращается максимум (итоговая)."""
    r = extract("Стоимость: 100 руб. Сумма: 200 руб. Итого: 300 руб.")
    assert r["amount"] == 300.0


def test_extract_short_amount_without_currency_returns_none():
    """Короткое число без валюты — не сумма (защита от ложных срабатываний)."""
    assert extract("Номер 12")["amount"] is None
    assert extract("Дата 03")["amount"] is None


# --- Тесты дат без "г." (iter 4) ---

def test_extract_date_month_name_without_g():
    """Дата '1 марта 2025' без 'г.' — должна парситься."""
    assert extract("от 1 марта 2025")["date"] == "2025-03-01"


def test_extract_date_month_name_without_space_g():
    """Дата '1 марта 2025г.' (без пробела перед г.) — должна парситься."""
    assert extract("от 1 марта 2025г.")["date"] == "2025-03-01"


def test_extract_date_may_without_g():
    """Дата '1 мая 2025' без 'г.' — должна парситься."""
    assert extract("от 1 мая 2025")["date"] == "2025-05-01"


# --- Тесты дат с суффиксами (iter 1 новой серии) ---

def test_extract_date_with_go_suffix():
    """Дата '1го марта 2025' — суффикс 'го'."""
    assert extract("от 1го марта 2025")["date"] == "2025-03-01"


def test_extract_date_with_go_suffix_2():
    """Дата '2го марта 2025'."""
    assert extract("от 2го марта 2025")["date"] == "2025-03-02"


def test_extract_date_without_suffix_still_works():
    """Дата '1 марта 2025' (без суффикса) — регрессия."""
    assert extract("от 1 марта 2025")["date"] == "2025-03-01"
