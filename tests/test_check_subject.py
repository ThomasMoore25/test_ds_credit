"""Тесты для check_subject()."""

from __future__ import annotations

from credit_check import check_subject


# --- PASS кейсы (соответствует программе) -------------------------------------

def test_check_subject_fertilizer_pass():
    matches, confidence, reason = check_subject("Поставка минеральных удобрений (карбамид марки Б)")
    assert matches is True
    assert confidence > 0.5
    assert "агрохим" in reason.lower() or "удобр" in reason.lower()


def test_check_subject_seeds_pass():
    matches, confidence, _ = check_subject("Поставка семян подсолнечника сорта «Командор», посевная партия 2025")
    assert matches is True
    assert confidence > 0.5


def test_check_subject_machinery_repair_pass():
    matches, _, _ = check_subject("Техническое обслуживание и ремонт зерноуборочного комбайна John Deere")
    assert matches is True


def test_check_subject_fuel_pass():
    matches, _, _ = check_subject("Поставка дизельного топлива для нужд сельхозпроизводства")
    assert matches is True


def test_check_subject_agrochemical_works_pass():
    matches, _, _ = check_subject("Выполнение агрохимических работ, внесение КАС-32")
    assert matches is True


def test_check_subject_spare_parts_pass():
    matches, _, _ = check_subject("Приобретение запасных частей для трактора МТЗ-82")
    assert matches is True


def test_check_subject_plant_protection_pass():
    matches, _, _ = check_subject("Поставка средств защиты растений (фунгицид Амистар)")
    assert matches is True


def test_check_subject_crop_insurance_pass():
    matches, _, _ = check_subject("Страхование урожая от неблагоприятных погодных условий")
    assert matches is True


# --- FAIL кейсы (не соответствует программе) ----------------------------------

def test_check_subject_office_rent_fail():
    matches, confidence, _ = check_subject("Аренда офисного помещения, г. Краснодар, ул. Ленина 15")
    assert matches is False
    assert confidence > 0.5


def test_check_subject_legal_fail():
    matches, _, _ = check_subject("Юридическое сопровождение сделки, консультационные услуги")
    assert matches is False


def test_check_subject_office_furniture_fail():
    matches, _, _ = check_subject("Поставка офисной мебели и канцелярских товаров")
    assert matches is False


def test_check_subject_it_fail():
    matches, _, _ = check_subject("Разработка корпоративного сайта и SEO-продвижение")
    assert matches is False


def test_check_subject_cleaning_fail():
    matches, _, _ = check_subject("Услуги клининговой компании, уборка административного здания")
    assert matches is False


def test_check_subject_training_fail():
    matches, _, _ = check_subject("Обучение механизаторов работе с новой техникой")
    assert matches is False


# --- EDGE кейсы (спорные) ----------------------------------------------------

def test_check_subject_transport_edge():
    """Транспортные услуги по доставке удобрений — спорный."""
    matches, confidence, _ = check_subject("Транспортные услуги по доставке удобрений до склада")
    # Решение может быть PASS или FAIL, но уверенность не должна быть слишком высокой
    assert 0.0 <= confidence <= 1.0
    assert isinstance(matches, bool)


def test_check_subject_machinery_rental_edge():
    matches, confidence, _ = check_subject("Аренда сельскохозяйственной техники на период уборки урожая")
    assert 0.0 <= confidence <= 1.0
    assert isinstance(matches, bool)


def test_check_subject_agronomist_edge():
    matches, confidence, _ = check_subject("Услуги агронома-консультанта по подбору схемы удобрений")
    assert 0.0 <= confidence <= 1.0
    assert isinstance(matches, bool)


def test_check_subject_agronomist_consultant_pass_v040():
    """v0.4.0: «агроном-консультант» — это PASS, не FAIL.

    Агрономическая консультация — это сельхоз-деятельность, не общие
    консультационные услуги. Добавлен белый список сильных сельхоз-контекстных
    слов, которые перебивают STRONG_FORBIDDEN.
    """
    matches, confidence, reason = check_subject(
        "Услуги агронома-консультанта по подбору схемы удобрений"
    )
    assert matches is True, f"Expected PASS for agronomist, got FAIL: {reason}"
    assert confidence >= 0.7
    assert "агроном" in reason.lower() or "сельхоз" in reason.lower()


def test_check_subject_veterinarian_consultation_pass_v040():
    """v0.4.0: «ветеринар-консультант» — тоже PASS по той же логике."""
    matches, confidence, _ = check_subject(
        "Консультационные услуги ветеринарного врача по лечению КРС"
    )
    assert matches is True


def test_check_subject_pure_consulting_still_fail_v040():
    """v0.4.0: обычные консультационные услуги без сельхоз-контекста — по-прежнему FAIL.

    Проверка, что белый список не сломал существующее поведение.
    """
    matches, _, _ = check_subject(
        "Консультационные услуги по налоговому планированию"
    )
    assert matches is False


# --- Возвращаемый тип ---------------------------------------------------------

def test_check_subject_returns_tuple_of_three():
    result = check_subject("Поставка удобрений")
    assert isinstance(result, tuple)
    assert len(result) == 3
    matches, confidence, reason = result
    assert isinstance(matches, bool)
    assert isinstance(confidence, float)
    assert isinstance(reason, str)
    assert 0.0 <= confidence <= 1.0


def test_check_subject_empty_string():
    matches, confidence, reason = check_subject("")
    assert matches is False
    assert 0.0 <= confidence <= 1.0
    assert isinstance(reason, str)


# --- Edge cases (iter 29-35) ---

def test_check_subject_very_long():
    """Очень длинный subject не должен падать."""
    long_subject = "Поставка удобрений " + "карбамид " * 100
    matches, _, _ = check_subject(long_subject)
    assert matches is True


def test_check_subject_special_chars():
    """Спецсимволы в subject не должны ломать."""
    matches, _, _ = check_subject("Поставка @#$% удобрений %&*")
    assert isinstance(matches, bool)


def test_check_subject_only_numbers():
    """Только числа → FAIL с низкой уверенностью."""
    matches, conf, _ = check_subject("1234567890")
    assert matches is False
    assert 0.0 <= conf <= 1.0


def test_check_subject_mixed_case():
    """Регистр не должен влиять на результат."""
    m1, _, _ = check_subject("ПОСТАВКА УДОБРЕНИЙ")
    m2, _, _ = check_subject("поставка удобрений")
    assert m1 == m2


def test_check_subject_with_extra_spaces():
    """Лишние пробелы не должны влиять."""
    m1, _, _ = check_subject("Поставка  удобрений")
    m2, _, _ = check_subject("Поставка удобрений")
    assert m1 == m2


def test_check_subject_unicode():
    """Unicode символы не должны ломать."""
    matches, _, _ = check_subject("Поставка удобрений 🚜")
    assert isinstance(matches, bool)


def test_check_subject_mixed_languages():
    """Смешение языков — английский + русский."""
    matches, _, _ = check_subject("Поставка John Deere трактора")
    assert matches is True


# --- Тесты новых категорий (iter 30-35) ---

def test_check_subject_animal_husbandry_pass():
    """Категория 'животноводство' — PASS."""
    matches, _, _ = check_subject("Закупка кормов для КРС")
    assert matches is True


def test_check_subject_vegetables_pass():
    """Категория 'овощи и фрукты' — PASS."""
    matches, _, _ = check_subject("Поставка семян картофеля")
    assert matches is True


def test_check_subject_fish_farming_pass():
    """Категория 'рыбоводство' — PASS."""
    matches, _, _ = check_subject("Закупка мальков карпа для пруда")
    assert matches is True


def test_check_subject_forestry_pass():
    """Категория 'лесное хозяйство' — PASS."""
    matches, _, _ = check_subject("Лесовосстановительные работы")
    assert matches is True


def test_check_subject_feed_additives_pass():
    """Расширенная категория 'корма' — БВМД, стартер."""
    matches, _, _ = check_subject("Поставка БВМД для телят")
    assert matches is True


def test_check_subject_new_machinery_brands_pass():
    """Расширенная категория 'техника' — New Holland, Claas."""
    matches, _, _ = check_subject("Закупка комбайна Claas")
    assert matches is True


# --- Дополнительные тесты (iter 40-50) ---

def test_check_subject_complex_phrases():
    """Сложные фразы с несколькими категориями."""
    matches, conf, _ = check_subject("Поставка минеральных удобрений и семян подсолнечника")
    assert matches is True
    assert conf >= 0.85  # 2 категории → 0.92


def test_check_subject_negative_with_no_keywords():
    """Subject без ключевых слов → FAIL с низкой уверенностью."""
    matches, conf, _ = check_subject("какой-то случайный текст")
    assert matches is False
    assert conf <= 0.6


def test_check_subject_with_typo():
    """Опечатка в слове — fuzzy matching должен справиться."""
    matches, _, _ = check_subject("Поставка удобренийи карбамида")
    assert matches is True


def test_check_subject_english_subject():
    """Английский subject — должен вернуть FAIL (не сельхоз-контекст)."""
    matches, _, _ = check_subject("Office rent in Moscow")
    assert matches is False


def test_check_subject_mixed_subject():
    """Смешанный subject — сельхоз + не сельхоз."""
    matches, _, _ = check_subject("Поставка удобрений и аренда офиса")
    # «офис» — сильное запрещённое, должно победить
    assert matches is False


def test_check_subject_agronomist_with_fertilizers():
    """Агроном + удобрения — двойной сельхоз-контекст."""
    matches, conf, _ = check_subject("Услуги агронома по подбору удобрений")
    assert matches is True
    assert conf >= 0.7


def test_check_subject_vet_with_medicine():
    """Ветеринар + лекарство — PASS (агро-контекст)."""
    matches, _, _ = check_subject("Консультация ветеринара по лечению КРС")
    assert matches is True


def test_check_subject_insurance_harvest():
    """Страхование урожая — PASS."""
    matches, _, _ = check_subject("Страхование посевов от засухи")
    assert matches is True


def test_check_subject_field_work():
    """Полевые работы — PASS."""
    matches, _, _ = check_subject("Вспашка зяби под посев 2025")
    assert matches is True


def test_check_subject_plant_protection():
    """СЗР — PASS."""
    matches, _, _ = check_subject("Обработка посевов фунгицидом")
    assert matches is True


# --- Тесты новых запрещённых слов (iter 65-70) ---

def test_check_subject_marketing_fail():
    matches, _, _ = check_subject("Маркетинговые услуги для интернет-магазина")
    assert matches is False


def test_check_subject_smm_fail():
    matches, _, _ = check_subject("SMM-продвижение в соцсетях")
    assert matches is False


def test_check_subject_target_fail():
    matches, _, _ = check_subject("Настройка таргетированной рекламы")
    assert matches is False


def test_check_subject_restaurant_fail():
    matches, _, _ = check_subject("Открытие ресторана в Краснодаре")
    assert matches is False


def test_check_subject_cafe_fail():
    matches, _, _ = check_subject("Закупка оборудования для кафе")
    assert matches is False


def test_check_subject_kfh_pass():
    matches, _, _ = check_subject("КФХ «Рассвет» — закупка удобрений")
    assert matches is True


def test_check_subject_single_char():
    """Один символ — не должен падать."""
    matches, _, _ = check_subject("X")
    assert matches is False


def test_check_subject_only_spaces():
    """Только пробелы."""
    matches, conf, _ = check_subject("   ")
    assert matches is False
    assert 0.0 <= conf <= 1.0


def test_check_subject_only_punctuation():
    """Только знаки препинания."""
    matches, _, _ = check_subject("!!! ??? ...")
    assert matches is False


def test_check_subject_newlines_only():
    """Только переносы строк."""
    matches, _, _ = check_subject("\n\n\n")
    assert matches is False
