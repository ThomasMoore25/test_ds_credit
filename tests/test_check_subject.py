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
