"""Прогон extract() и classify() по всем файлам датасета.

Сверка с ожидаемыми значениями из dataset/README.md.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from credit_check import check_subject, classify, extract

DATASET_DIR = Path(__file__).resolve().parent.parent / "dataset"


# Ожидаемые результаты extract() из dataset/README.md
EXPECTED_EXTRACT: dict[str, dict] = {
    "contract_001.txt": {
        "amount": 1_250_000.0,
        "date": "2025-03-01",
        "inn": "7701234567",
        "contractor": "ООО «ТехАгро»",
    },
    "invoice_001.txt": {
        "amount": 1_250_000.0,
        "date": "2025-03-03",
        "inn": "7701234567",
        "contractor": "ООО «ТехАгро»",
    },
    "invoice_002.txt": {
        "amount": 900_000.0,
        "date": "2025-02-28",  # ожидаемое значение из README
        "inn": "5047123456",
        "contractor": "АО «АгроСнаб»",
    },
    "act_001.txt": {
        "amount": 1_250_000.0,
        "date": "2025-03-24",
        "inn": "7701234567",
        "contractor": "ООО «ТехАгро»",
    },
    "act_002.txt": {
        "amount": 500_000.0,
        "date": "2025-04-01",
        "inn": "504712345678",
        "contractor": "ИП Смирнов В.А.",
    },
}

# Ожидаемые классы для classify() — спецификация датасета
EXPECTED_CLASSIFY: dict[str, str] = {
    "contract_001.txt": "contract",
    "spec_001.txt": "spec",
    "invoice_001.txt": "invoice",
    "invoice_002.txt": "invoice",
    "act_001.txt": "act",
    "act_002.txt": "act",
    "scan_ocr_001.txt": "unknown",
}


def _read(name: str) -> str:
    return (DATASET_DIR / name).read_text(encoding="utf-8")


# --- Параметризованный прогон extract() ---------------------------------------

@pytest.mark.parametrize("filename,expected", EXPECTED_EXTRACT.items())
def test_dataset_extract(filename: str, expected: dict) -> None:
    """extract() на файле датасета должен вернуть ожидаемые поля."""
    text = _read(filename)
    result = extract(text)

    # amount
    if expected["amount"] is None:
        assert result["amount"] is None, f"{filename}: amount expected None"
    else:
        assert result["amount"] == pytest.approx(expected["amount"]), (
            f"{filename}: amount expected {expected['amount']}, got {result['amount']}"
        )

    # date
    assert result["date"] == expected["date"], (
        f"{filename}: date expected {expected['date']}, got {result['date']}"
    )

    # inn
    assert result["inn"] == expected["inn"], (
        f"{filename}: inn expected {expected['inn']}, got {result['inn']}"
    )

    # contractor
    assert result["contractor"] == expected["contractor"], (
        f"{filename}: contractor expected {expected['contractor']!r}, "
        f"got {result['contractor']!r}"
    )


# --- Параметризованный прогон classify() --------------------------------------

@pytest.mark.parametrize("filename,expected_type", EXPECTED_CLASSIFY.items())
def test_dataset_classify(filename: str, expected_type: str) -> None:
    """classify() на файле датасета должен вернуть ожидаемый тип."""
    text = _read(filename)
    doc_type, confidence = classify(text)
    assert doc_type == expected_type, (
        f"{filename}: type expected {expected_type}, got {doc_type} (conf={confidence:.3f})"
    )
    assert 0.0 <= confidence <= 1.0


# --- OCR-мусор: проверяем, что INN не извлекается (с буквами вместо цифр) -----

def test_dataset_scan_ocr_inn_is_none() -> None:
    """scan_ocr_001.txt: ИНН с буквой 'l' вместо '1' не должен валидироваться."""
    text = _read("scan_ocr_001.txt")
    result = extract(text)
    assert result["inn"] is None, (
        f"OCR-мусор: inn должен быть None, got {result['inn']!r}"
    )


# --- subjects_test.txt: прогон check_subject() по 15 примерам -----------------

def _parse_subjects_test() -> list[tuple[str, str]]:
    """Парсит subjects_test.txt → [(status, subject), ...]."""
    text = _read("subjects_test.txt")
    out: list[tuple[str, str]] = []
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if "|" not in line:
            continue
        status, subject = line.split("|", 1)
        status = status.strip().upper()
        subject = subject.strip()
        if status in {"PASS", "FAIL", "EDGE"} and subject:
            out.append((status, subject))
    return out


_SUBJECTS = _parse_subjects_test()


@pytest.mark.parametrize("status,subject", _SUBJECTS)
def test_dataset_subjects(status: str, subject: str) -> None:
    """check_subject() на файле subjects_test.txt."""
    matches, confidence, reason = check_subject(subject)

    # Базовые инварианты
    assert isinstance(matches, bool)
    assert 0.0 <= confidence <= 1.0
    assert isinstance(reason, str) and len(reason) > 0

    # Для PASS/FAIL проверяем совпадение (EDGE — спорные, допускаем любой исход)
    if status == "PASS":
        assert matches is True, (
            f"PASS expected, got FAIL for {subject!r}: {reason}"
        )
    elif status == "FAIL":
        assert matches is False, (
            f"FAIL expected, got PASS for {subject!r}: {reason}"
        )
    # EDGE — нет жёсткого ассерта, проверяем только типы


# --- Дополнительные проверки датасета (iter 59-65) ---

def test_all_dataset_files_have_classify_result():
    """Все файлы датасета должны возвращать валидный тип (не None)."""
    for fname in sorted(DATASET_DIR.glob("*.txt")):
        if fname.name == "subjects_test.txt":
            continue
        text = _read(fname.name)
        doc_type, _ = classify(text)
        assert doc_type in {"contract", "spec", "invoice", "act", "unknown"}, (
            f"{fname.name}: invalid doc_type {doc_type}"
        )


def test_all_dataset_files_have_confidence_in_range():
    """confidence classify должен быть в [0, 1]."""
    for fname in sorted(DATASET_DIR.glob("*.txt")):
        if fname.name == "subjects_test.txt":
            continue
        text = _read(fname.name)
        _, conf = classify(text)
        assert 0.0 <= conf <= 1.0, f"{fname.name}: conf {conf} out of range"


def test_all_extract_results_have_all_keys():
    """extract всегда возвращает все 5 ключей."""
    for fname in sorted(DATASET_DIR.glob("*.txt")):
        if fname.name == "subjects_test.txt":
            continue
        text = _read(fname.name)
        result = extract(text)
        assert set(result.keys()) == {"amount", "date", "inn", "contractor", "subject"}


def test_all_amounts_are_positive_or_none():
    """amount должен быть > 0 или None."""
    for fname in sorted(DATASET_DIR.glob("*.txt")):
        if fname.name == "subjects_test.txt":
            continue
        text = _read(fname.name)
        result = extract(text)
        if result["amount"] is not None:
            assert result["amount"] > 0, f"{fname.name}: amount {result['amount']} not positive"


def test_all_dates_are_iso_format():
    """date должен быть None или ISO YYYY-MM-DD."""
    import re
    iso_re = re.compile(r"^\d{4}-\d{2}-\d{2}$")
    for fname in sorted(DATASET_DIR.glob("*.txt")):
        if fname.name == "subjects_test.txt":
            continue
        text = _read(fname.name)
        result = extract(text)
        if result["date"] is not None:
            assert iso_re.match(result["date"]), f"{fname.name}: date {result['date']} not ISO"


def test_all_inn_are_10_or_12_digits():
    """ИНН должен быть 10 или 12 цифр или None."""
    for fname in sorted(DATASET_DIR.glob("*.txt")):
        if fname.name == "subjects_test.txt":
            continue
        text = _read(fname.name)
        result = extract(text)
        if result["inn"] is not None:
            assert len(result["inn"]) in (10, 12), f"{fname.name}: INN {result['inn']} wrong length"
            assert result["inn"].isdigit(), f"{fname.name}: INN {result['inn']} not digits"


def test_invoice_002_full_extract():
    """Полная проверка invoice_002 — все поля."""
    text = _read("invoice_002.txt")
    r = extract(text)
    assert r["amount"] == 900_000.0
    assert r["date"] == "2025-02-28"
    assert r["inn"] == "5047123456"
    assert r["contractor"] == "АО «АгроСнаб»"
    assert r["subject"] is not None
    assert "семян" in r["subject"].lower()


def test_act_002_full_extract():
    """Полная проверка act_002 — все поля."""
    text = _read("act_002.txt")
    r = extract(text)
    assert r["amount"] == 500_000.0
    assert r["date"] == "2025-04-01"
    assert r["inn"] == "504712345678"
    assert r["contractor"] == "ИП Смирнов В.А."
    assert r["subject"] is not None
    assert "удобр" in r["subject"].lower() or "внесен" in r["subject"].lower()


def test_scan_ocr_returns_none_for_critical_fields():
    """scan_ocr возвращает None для amount, inn, contractor."""
    text = _read("scan_ocr_001.txt")
    r = extract(text)
    assert r["amount"] is None
    assert r["inn"] is None
    assert r["contractor"] is None
