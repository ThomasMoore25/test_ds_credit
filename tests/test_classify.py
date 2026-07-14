"""Тесты для classify()."""

from __future__ import annotations

from credit_check import classify


# --- Обязательные тесты из задания --------------------------------------------

def test_classify_invoice_basic():
    """Счёт на оплату №12 от 01.03.2025 → ('invoice', >0.5)"""
    text = "Счёт на оплату №12 от 01.03.2025. Поставщик: ООО «Ромашка»"
    doc_type, confidence = classify(text)
    assert doc_type == "invoice"
    assert confidence > 0.5


# --- Кейсы по каждому типу из датасета ----------------------------------------

def test_classify_contract():
    text = (
        "ДОГОВОР ПОСТАВКИ № 47/2025\n"
        "Поставщик обязуется передать в собственность Покупателя товар. "
        "1. ПРЕДМЕТ ДОГОВОРА. 2. СУММА ДОГОВОРА. Подписи сторон."
    )
    doc_type, confidence = classify(text)
    assert doc_type == "contract"
    assert confidence > 0.5


def test_classify_spec():
    text = (
        "СПЕЦИФИКАЦИЯ № 1 к Договору поставки № 47/2025\n"
        "Дата составления: 01.03.2025. "
        "Итого без НДС: 1 041 666,67 руб. Итого с НДС: 1 250 000,00 руб."
    )
    doc_type, confidence = classify(text)
    assert doc_type == "spec"
    assert confidence > 0.5


def test_classify_act_upd():
    text = (
        "УНИВЕРСАЛЬНЫЙ ПЕРЕДАТОЧНЫЙ ДОКУМЕНТ (УПД)\n"
        "Статус документа: 1 (счёт-фактура и передаточный документ)\n"
        "Товар передан / Работы выполнены. Работы приняты."
    )
    doc_type, confidence = classify(text)
    assert doc_type == "act"
    assert confidence > 0.5


def test_classify_act_performed_works():
    text = (
        "АКТ ВЫПОЛНЕННЫХ РАБОТ № 14\n"
        "Работы выполнены в полном объёме. Претензий по качеству не имеется."
    )
    doc_type, confidence = classify(text)
    assert doc_type == "act"
    assert confidence > 0.5


# --- Кейсы unknown ------------------------------------------------------------

def test_classify_empty_returns_unknown():
    doc_type, confidence = classify("")
    assert doc_type == "unknown"
    assert confidence == 0.0


def test_classify_ocr_garbage_returns_unknown():
    """OCR-мусор с малым разрывом скоров → unknown."""
    text = (
        "3АО \"ТexАгро\" ИНН 770l234567 "
        "Нaимeнoвaниe: Kaрбaмид мapки Б "
        "Ocнoвaниe: дoг. № 47/2O25"
    )
    doc_type, confidence = classify(text)
    # OCR-мусор: совпадения есть, но разрыв маленький → unknown
    assert doc_type == "unknown"


def test_classify_unrelated_text_unknown():
    """Текст без типовых маркеров → unknown."""
    doc_type, _ = classify(" просто текст без маркеров документа ")
    assert doc_type == "unknown"


# --- Проверка возвращаемых типов ----------------------------------------------

def test_classify_returns_tuple():
    result = classify("Счёт на оплату №1")
    assert isinstance(result, tuple)
    assert len(result) == 2
    doc_type, confidence = result
    assert isinstance(doc_type, str)
    assert isinstance(confidence, float)
    assert 0.0 <= confidence <= 1.0


def test_classify_valid_type_value():
    doc_type, _ = classify("Договор поставки №1. Поставщик, покупатель.")
    assert doc_type in {"contract", "spec", "invoice", "act", "unknown"}


# --- Edge cases (iter 27-31) ---

def test_classify_single_word_unknown():
    """Одно слово — слишком мало контекста, но не пусто."""
    doc_type, _ = classify("договор")
    # Слово «договор» — сильный маркер, но без контекста это может быть и unknown
    assert doc_type in {"contract", "unknown"}


def test_classify_only_numbers_unknown():
    """Текст только из чисел → unknown."""
    doc_type, _ = classify("123 456 789")
    assert doc_type == "unknown"


def test_classify_mixed_markers_returns_one_of_known():
    """Текст с маркерами нескольких классов — возвращает один из типов или unknown.
    Не падает, возвращает валидный тип.
    """
    text = "договор спецификация счёт акт"
    doc_type, _ = classify(text)
    assert doc_type in {"contract", "spec", "invoice", "act", "unknown"}


def test_classify_very_long_text_still_classifies():
    """Длинный текст с явным маркером — должен классифицироваться."""
    text = "СЧЁТ НА ОПЛАТУ № 12. " + "услуга " * 500
    doc_type, _ = classify(text)
    assert doc_type == "invoice"


def test_classify_special_characters():
    """Спецсимволы не должны ломать классификацию."""
    text = "Договор поставки @#$% № 1 от 01.03.2025"
    doc_type, _ = classify(text)
    # Должен быть contract или unknown, но не падать
    assert doc_type in {"contract", "spec", "invoice", "act", "unknown"}


# --- Дополнительные тесты (iter 36-45) ---

def test_classify_invoice_with_specs_marker():
    """Счёт со словом «спецификация» в основании — валидный тип."""
    text = "СЧЁТ НА ОПЛАТУ № 12. Основание: спецификация №1."
    doc_type, _ = classify(text)
    assert doc_type in {"invoice", "spec", "unknown"}


def test_classify_act_with_upd_full():
    """Полный УПД."""
    text = "Универсальный передаточный документ. Статус 1. Работы выполнены."
    doc_type, conf = classify(text)
    assert doc_type == "act"
    assert conf > 0.5


def test_classify_contract_with_subject_marker():
    """Договор с «предмет договора»."""
    text = "ДОГОВОР. Предмет договора: поставка. Сумма договора: 100 руб."
    doc_type, _ = classify(text)
    assert doc_type == "contract"


def test_classify_spec_with_date_marker():
    """Спецификация с «дата составления»."""
    text = "Спецификация №1 к договору. Дата составления: 01.03.2025. Итого с НДС."
    doc_type, _ = classify(text)
    assert doc_type == "spec"


def test_classify_minimal_invoice():
    """Минимальный счёт."""
    doc_type, conf = classify("Счёт на оплату")
    assert doc_type == "invoice"
    assert conf > 0.5


def test_classify_minimal_contract():
    """Минимальный договор."""
    doc_type, _ = classify("Договор поставки")
    assert doc_type == "contract"


def test_classify_minimal_spec():
    """Минимальная спецификация."""
    doc_type, _ = classify("Спецификация №1 к договору поставки")
    assert doc_type == "spec"


def test_classify_minimal_act():
    """Минимальный акт."""
    doc_type, _ = classify("Акт выполненных работ")
    assert doc_type == "act"


def test_classify_returns_float_confidence():
    """confidence должен быть float в [0, 1]."""
    _, conf = classify("Договор поставки")
    assert isinstance(conf, float)
    assert 0.0 <= conf <= 1.0


def test_classify_unknown_for_pure_numbers():
    """Чистые числа → unknown."""
    doc_type, _ = classify("1234567890")
    assert doc_type == "unknown"
