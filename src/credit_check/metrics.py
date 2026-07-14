"""Метрики качества для extract/classify/check_subject.

Прогоняет функции на датасете и считает:
    - extract: accuracy по каждому полю (amount/date/inn/contractor/subject)
    - classify: accuracy + доля unknown
    - check_subject: accuracy на PASS/FAIL + распределение EDGE

Запуск:
    python -m credit_check.metrics
    # или
    python scripts/compute_metrics.py
"""

from __future__ import annotations

import sys
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Final

from credit_check import check_subject, classify, extract

DATASET_DIR: Final[Path] = Path(__file__).resolve().parent.parent.parent / "dataset"

# Ожидаемые значения extract() из dataset/README.md
_EXPECTED_EXTRACT: Final[dict[str, dict]] = {
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
        "date": "2025-02-28",
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

_EXPECTED_CLASSIFY: Final[dict[str, str]] = {
    "contract_001.txt": "contract",
    "spec_001.txt": "spec",
    "invoice_001.txt": "invoice",
    "invoice_002.txt": "invoice",
    "act_001.txt": "act",
    "act_002.txt": "act",
    "scan_ocr_001.txt": "unknown",
}


@dataclass
class FieldMetric:
    """Метрика по одному полю extract()."""
    field: str
    correct: int
    total: int

    @property
    def accuracy(self) -> float:
        return self.correct / self.total if self.total else 0.0


def _read(name: str) -> str:
    return (DATASET_DIR / name).read_text(encoding="utf-8")


def compute_extract_metrics() -> dict[str, FieldMetric]:
    """Считает accuracy по каждому полю extract()."""
    counters = {f: FieldMetric(f, 0, 0) for f in ("amount", "date", "inn", "contractor")}
    for fname, expected in _EXPECTED_EXTRACT.items():
        text = _read(fname)
        result = extract(text)
        for field in counters:
            counters[field].total += 1
            if field == "amount":
                got = result[field]
                want = expected[field]
                if got is None and want is None:
                    counters[field].correct += 1
                elif got is not None and want is not None and abs(got - want) < 0.01:
                    counters[field].correct += 1
            else:
                if result[field] == expected[field]:
                    counters[field].correct += 1
    return counters


def compute_extract_precision() -> dict[str, float]:
    """Считает precision по каждому полю extract().

    Precision = TP / (TP + FP), где:
        TP — поле извлечено и совпадает с ожидаемым
        FP — поле извлечено, но не совпадает (включая None vs not-None)
    Для полей, где expected = None, считаем TP = поле None, FP = поле not-None.
    """
    counters = {f: {"tp": 0, "fp": 0} for f in ("amount", "date", "inn", "contractor")}
    for fname, expected in _EXPECTED_EXTRACT.items():
        text = _read(fname)
        result = extract(text)
        for field in counters:
            got = result[field]
            want = expected[field]
            if field == "amount":
                if got is None and want is None:
                    counters[field]["tp"] += 1
                elif got is not None and want is not None and abs(got - want) < 0.01:
                    counters[field]["tp"] += 1
                else:
                    counters[field]["fp"] += 1
            else:
                if got == want:
                    counters[field]["tp"] += 1
                else:
                    counters[field]["fp"] += 1
    return {
        f: (v["tp"] / (v["tp"] + v["fp"]) if (v["tp"] + v["fp"]) > 0 else 0.0)
        for f, v in counters.items()
    }


def compute_classify_avg_confidence() -> float:
    """Средняя confidence classify по датасету (без unknown)."""
    confs = []
    for fname, expected in _EXPECTED_CLASSIFY.items():
        text = _read(fname)
        _, conf = classify(text)
        if expected != "unknown":
            confs.append(conf)
    return sum(confs) / len(confs) if confs else 0.0


def compute_classify_metrics() -> dict[str, float]:
    """Считает accuracy и долю unknown для classify()."""
    correct = 0
    total = 0
    unknown_count = 0
    for fname, expected in _EXPECTED_CLASSIFY.items():
        text = _read(fname)
        doc_type, _ = classify(text)
        total += 1
        if doc_type == expected:
            correct += 1
        if doc_type == "unknown":
            unknown_count += 1
    return {
        "accuracy": correct / total if total else 0.0,
        "unknown_rate": unknown_count / total if total else 0.0,
    }


def compute_check_subject_metrics() -> dict[str, float]:
    """Считает accuracy на PASS/FAIL и распределение EDGE для check_subject()."""
    text = _read("subjects_test.txt")
    pass_correct = 0
    pass_total = 0
    fail_correct = 0
    fail_total = 0
    edge_total = 0
    edge_distribution: Counter[str] = Counter()

    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "|" not in line:
            continue
        status, subject = line.split("|", 1)
        status = status.strip().upper()
        subject = subject.strip()
        matches, confidence, _ = check_subject(subject)
        if status == "PASS":
            pass_total += 1
            if matches:
                pass_correct += 1
        elif status == "FAIL":
            fail_total += 1
            if not matches:
                fail_correct += 1
        elif status == "EDGE":
            edge_total += 1
            label = "PASS" if matches else "FAIL"
            edge_distribution[label] += 1

    # F1 для бинарной классификации PASS/FAIL
    tp = pass_correct  # PASS предсказан как PASS
    fn = pass_total - pass_correct  # PASS предсказан как FAIL
    fp = fail_total - fail_correct  # FAIL предсказан как PASS
    tn = fail_correct  # FAIL предсказан как FAIL
    precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0

    return {
        "pass_accuracy": pass_correct / pass_total if pass_total else 0.0,
        "fail_accuracy": fail_correct / fail_total if fail_total else 0.0,
        "precision": precision,
        "recall": recall,
        "f1": f1,
        "confusion_matrix": {"tp": tp, "fp": fp, "fn": fn, "tn": tn},
        "edge_total": float(edge_total),
        "edge_pass_count": float(edge_distribution.get("PASS", 0)),
        "edge_fail_count": float(edge_distribution.get("FAIL", 0)),
        "edge_low_confidence_rate": _compute_edge_low_confidence_rate(text),
    }


def _compute_edge_low_confidence_rate(text: str) -> float:
    """Доля EDGE-кейсов с confidence < 0.7 (требуется ручная проверка)."""
    edge_total = 0
    low_conf = 0
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "|" not in line:
            continue
        status, subject = line.split("|", 1)
        status = status.strip().upper()
        subject = subject.strip()
        if status != "EDGE":
            continue
        edge_total += 1
        _, confidence, _ = check_subject(subject)
        if confidence < 0.7:
            low_conf += 1
    return low_conf / edge_total if edge_total else 0.0


def format_metrics() -> str:
    """Форматирует все метрики в строку для вывода."""
    lines = ["# Метрики качества (v0.6.0)\n"]

    lines.append("## extract() — accuracy по полям\n")
    lines.append("| Поле | Accuracy | Correct/Total |")
    lines.append("|---|---|---|")
    for m in compute_extract_metrics().values():
        lines.append(f"| {m.field} | {m.accuracy:.1%} | {m.correct}/{m.total} |")

    lines.append("\n## extract() — precision по полям\n")
    lines.append("| Поле | Precision |")
    lines.append("|---|---|")
    for f, p in compute_extract_precision().items():
        lines.append(f"| {f} | {p:.1%} |")

    lines.append("\n## classify() — общие метрики\n")
    cm = compute_classify_metrics()
    lines.append(f"- Accuracy: **{cm['accuracy']:.1%}**")
    lines.append(f"- Доля unknown: **{cm['unknown_rate']:.1%}**")
    lines.append(f"- Средняя confidence (без unknown): **{compute_classify_avg_confidence():.1%}**")

    lines.append("\n## check_subject() — метрики на subjects_test.txt\n")
    sm = compute_check_subject_metrics()
    lines.append(f"- PASS accuracy: **{sm['pass_accuracy']:.1%}**")
    lines.append(f"- FAIL accuracy: **{sm['fail_accuracy']:.1%}**")
    lines.append(f"- Precision: **{sm['precision']:.1%}**")
    lines.append(f"- Recall: **{sm['recall']:.1%}**")
    lines.append(f"- F1: **{sm['f1']:.1%}**")
    cm = sm["confusion_matrix"]
    lines.append(
        f"- Confusion matrix: TP={cm['tp']} FP={cm['fp']} FN={cm['fn']} TN={cm['tn']}"
    )
    lines.append(f"- EDGE всего: {int(sm['edge_total'])}")
    lines.append(f"  - из них PASS: {int(sm['edge_pass_count'])}")
    lines.append(f"  - из них FAIL: {int(sm['edge_fail_count'])}")
    lines.append(
        f"- Доля EDGE с confidence < 0.7 (ручная проверка): "
        f"**{sm['edge_low_confidence_rate']:.1%}**"
    )

    return "\n".join(lines)


def main() -> int:
    print(format_metrics())
    return 0


if __name__ == "__main__":
    sys.exit(main())
