#!/usr/bin/env python3
"""Генерация 3 графиков для README.

Сохраняет PNG в docs/images/:
    1. classify_confidence.png   — confidence classify по 7 файлам датасета
    2. check_subject_results.png — результаты check_subject на 15 предметах
    3. classify_threshold_experiment.png — эксперимент с порогом top1-top2

Запуск:
    python scripts/generate_plots.py
"""
from __future__ import annotations

import pathlib
import sys

# Добавляем src в path, чтобы скрипт можно было запускать из корня репозитория
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / "src"))

import matplotlib.font_manager as fm  # noqa: E402

# Регистрируем DejaVu Sans — есть в системе и поддерживает кириллицу
try:
    fm.fontManager.addfont("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf")
except Exception:
    pass  # на CI/Linux без этого файла DejaVu всё равно доступен по умолчанию

import matplotlib.pyplot as plt  # noqa: E402

# DejaVu Sans поддерживает кириллицу из коробки
plt.rcParams["font.sans-serif"] = ["DejaVu Sans", "Liberation Sans", "sans-serif"]
plt.rcParams["axes.unicode_minus"] = False

from credit_check import check_subject, classify, extract  # noqa: E402
from credit_check.classify import _MARKERS, _score_class, _softmax  # noqa: E402

DATASET = pathlib.Path(__file__).resolve().parent.parent / "dataset"
OUT = pathlib.Path(__file__).resolve().parent.parent / "docs" / "images"
OUT.mkdir(parents=True, exist_ok=True)


# --- Данные ------------------------------------------------------------------

# Ожидаемые классы для classify
CLASSIFY_EXPECTED = {
    "contract_001.txt": "contract",
    "spec_001.txt": "spec",
    "invoice_001.txt": "invoice",
    "invoice_002.txt": "invoice",
    "act_001.txt": "act",
    "act_002.txt": "act",
    "scan_ocr_001.txt": "unknown",
}


def _read(name: str) -> str:
    return (DATASET / name).read_text(encoding="utf-8")


# --- График 1: confidence classify по датасету --------------------------------


def plot_classify_confidence() -> pathlib.Path:
    files = list(CLASSIFY_EXPECTED.keys())
    confidences = []
    types = []
    expected = []
    for f in files:
        text = _read(f)
        dt, conf = classify(text)
        confidences.append(conf)
        types.append(dt)
        expected.append(CLASSIFY_EXPECTED[f])

    fig, ax = plt.subplots(figsize=(11, 5), constrained_layout=True)
    colors = ["#2ecc71" if t == e else "#e74c3c" for t, e in zip(types, expected)]
    # Для unknown ожидается unknown — тоже зелёный
    colors = [
        "#2ecc71" if (t == e or (e == "unknown" and t == "unknown")) else "#e74c3c"
        for t, e in zip(types, expected)
    ]
    bars = ax.bar(range(len(files)), confidences, color=colors, edgecolor="black", linewidth=0.5)
    ax.set_xticks(range(len(files)))
    ax.set_xticklabels(files, rotation=30, ha="right", fontsize=9)
    ax.set_ylabel("Confidence", fontsize=11)
    ax.set_title("Confidence classify() по файлам датасета", fontsize=12, pad=10)
    ax.set_ylim(0, 1.05)
    ax.axhline(0.5, color="gray", linestyle="--", linewidth=0.8, alpha=0.7)
    ax.text(len(files) - 0.5, 0.52, "порог 0.5", color="gray", fontsize=8, ha="right")

    # Подписи над столбцами
    for i, (bar, t, c) in enumerate(zip(bars, types, confidences)):
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            c + 0.02,
            f"{t}\n{c:.2f}",
            ha="center",
            va="bottom",
            fontsize=8,
        )

    # Легенда
    from matplotlib.patches import Patch
    legend_elements = [
        Patch(facecolor="#2ecc71", edgecolor="black", label="Совпало с ожидаемым"),
        Patch(facecolor="#e74c3c", edgecolor="black", label="Не совпало"),
    ]
    ax.legend(handles=legend_elements, loc="upper right", fontsize=9)

    out = OUT / "classify_confidence.png"
    fig.savefig(out, dpi=120)
    plt.close(fig)
    return out


# --- График 2: результаты check_subject ---------------------------------------


def plot_check_subject_results() -> pathlib.Path:
    text = _read("subjects_test.txt")
    items: list[tuple[str, str, bool, float]] = []  # (status, subject, matches, conf)
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "|" not in line:
            continue
        status, subject = line.split("|", 1)
        status = status.strip().upper()
        subject = subject.strip()
        matches, conf, _ = check_subject(subject)
        items.append((status, subject, matches, conf))

    # Группируем по статусу
    statuses = ["PASS", "FAIL", "EDGE"]
    colors_map = {"PASS": "#2ecc71", "FAIL": "#e74c3c", "EDGE": "#f39c12"}

    fig, ax = plt.subplots(figsize=(12, 6), constrained_layout=True)
    y_pos = list(range(len(items)))
    bar_colors = [colors_map[s] for s, _, _, _ in items]
    confs = [c for _, _, _, c in items]
    labels = [f"{s}: {subj[:40]}{'...' if len(subj) > 40 else ''}" for s, subj, _, _ in items]

    bars = ax.barh(y_pos, confs, color=bar_colors, edgecolor="black", linewidth=0.5)
    ax.set_yticks(y_pos)
    ax.set_yticklabels(labels, fontsize=8)
    ax.invert_yaxis()
    ax.set_xlabel("Confidence", fontsize=11)
    ax.set_title("Результаты check_subject() на 15 предметах оплаты", fontsize=12, pad=10)
    ax.set_xlim(0, 1.05)
    ax.axvline(0.7, color="gray", linestyle="--", linewidth=0.8, alpha=0.7)
    ax.text(0.71, -0.5, "порог ручной проверки 0.7", color="gray", fontsize=8, rotation=90, va="top")

    # Подписи — PASS/FAIL вместо numeric
    for i, (_, _, matches, c) in enumerate(items):
        label = "PASS" if matches else "FAIL"
        ax.text(c + 0.01, i, f"{label} ({c:.2f})", va="center", fontsize=8)

    # Легенда
    from matplotlib.patches import Patch
    legend_elements = [
        Patch(facecolor=colors_map["PASS"], edgecolor="black", label="PASS (должен соответствовать)"),
        Patch(facecolor=colors_map["FAIL"], edgecolor="black", label="FAIL (не должен соответствовать)"),
        Patch(facecolor=colors_map["EDGE"], edgecolor="black", label="EDGE (спорный)"),
    ]
    ax.legend(handles=legend_elements, loc="lower right", fontsize=9)

    out = OUT / "check_subject_results.png"
    fig.savefig(out, dpi=120)
    plt.close(fig)
    return out


# --- График 3: эксперимент с порогом classify ----------------------------------


def _classify_with_threshold(text: str, threshold: float) -> tuple[str, float]:
    """Классификация с произвольным порогом top1-top2 (для эксперимента)."""
    import math
    raw_scores = {cls: _score_class(text, pats) for cls, pats in _MARKERS.items()}
    if max(raw_scores.values()) < 2.0:
        return ("unknown", 0.0)
    probs = _softmax(raw_scores)
    ranked = sorted(probs.items(), key=lambda kv: kv[1], reverse=True)
    top1_cls, top1_prob = ranked[0]
    top2_prob = ranked[1][1] if len(ranked) > 1 else 0.0
    if (top1_prob - top2_prob) < threshold:
        return ("unknown", top1_prob)
    return (top1_cls, top1_prob)


def plot_threshold_experiment() -> pathlib.Path:
    thresholds = [0.05, 0.10, 0.15, 0.20, 0.25, 0.30, 0.40, 0.50]
    unknown_counts = []
    error_counts = []
    total = len(CLASSIFY_EXPECTED)

    for thr in thresholds:
        unk = 0
        err = 0
        for fname, expected in CLASSIFY_EXPECTED.items():
            text = _read(fname)
            dt, _ = _classify_with_threshold(text, thr)
            if dt == "unknown":
                unk += 1
                # Если expected != unknown, это ошибка (лишний unknown)
                if expected != "unknown":
                    err += 1
            else:
                # Если предсказание не совпало с expected — ошибка
                if dt != expected:
                    err += 1
        unknown_counts.append(unk)
        error_counts.append(err)

    fig, ax = plt.subplots(figsize=(10, 5.5), constrained_layout=True)
    x = list(range(len(thresholds)))
    width = 0.4
    bars1 = ax.bar([i - width / 2 for i in x], unknown_counts, width,
                    label="unknown (включая корректные)", color="#3498db", edgecolor="black", linewidth=0.5)
    bars2 = ax.bar([i + width / 2 for i in x], error_counts, width,
                    label="ошибки классификации", color="#e74c3c", edgecolor="black", linewidth=0.5)

    ax.set_xticks(x)
    ax.set_xticklabels([f"{t:.2f}" for t in thresholds])
    ax.set_xlabel("Порог top1-top2", fontsize=11)
    ax.set_ylabel("Число файлов (всего 7)", fontsize=11)
    ax.set_title("Эксперимент с порогом classify(): unknown vs ошибки", fontsize=12, pad=10)
    ax.legend(loc="upper right", fontsize=9)
    ax.set_ylim(0, max(max(unknown_counts), max(error_counts)) + 1.5)

    # Подписи значений
    for bar in bars1:
        h = bar.get_height()
        if h > 0:
            ax.text(bar.get_x() + bar.get_width() / 2, h + 0.1, f"{int(h)}",
                    ha="center", fontsize=9)
    for bar in bars2:
        h = bar.get_height()
        if h > 0:
            ax.text(bar.get_x() + bar.get_width() / 2, h + 0.1, f"{int(h)}",
                    ha="center", fontsize=9)

    # Выделим выбранный порог 0.15
    chosen_idx = thresholds.index(0.15)
    ax.axvspan(chosen_idx - 0.45, chosen_idx + 0.45, alpha=0.15, color="#2ecc71")
    ax.text(chosen_idx, -0.8, "выбран 0.15", color="#2ecc71", fontsize=9, ha="center", fontweight="bold")

    out = OUT / "classify_threshold_experiment.png"
    fig.savefig(out, dpi=120)
    plt.close(fig)
    return out


def plot_check_subject_confusion_matrix() -> pathlib.Path:
    """График confusion matrix для check_subject на PASS/FAIL."""
    from credit_check.metrics import compute_check_subject_metrics
    sm = compute_check_subject_metrics()
    cm = sm["confusion_matrix"]

    fig, ax = plt.subplots(figsize=(5, 4.5), constrained_layout=True)
    matrix = [[cm["tp"], cm["fp"]], [cm["fn"], cm["tn"]]]
    im = ax.imshow(matrix, cmap="Greens", vmin=0, vmax=max(cm.values()) + 1)

    ax.set_xticks([0, 1])
    ax.set_yticks([0, 1])
    ax.set_xticklabels(["PASS (expected)", "FAIL (expected)"])
    ax.set_yticklabels(["PASS (predicted)", "FAIL (predicted)"])
    ax.set_xlabel("Ожидаемый результат")
    ax.set_ylabel("Предсказанный результат")
    ax.set_title("Confusion matrix: check_subject()")

    for i in range(2):
        for j in range(2):
            ax.text(j, i, str(matrix[i][j]), ha="center", va="center",
                    fontsize=16, color="black" if matrix[i][j] > 0 else "gray")

    out = OUT / "check_subject_confusion_matrix.png"
    fig.savefig(out, dpi=120)
    plt.close(fig)
    return out

def plot_check_subject_confidence_distribution() -> pathlib.Path:
    """Гистограмма распределения confidence в check_subject."""
    text = _read("subjects_test.txt")
    confs_pass = []
    confs_fail = []
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "|" not in line:
            continue
        status, subject = line.split("|", 1)
        status = status.strip().upper()
        matches, conf, _ = check_subject(subject.strip())
        if matches:
            confs_pass.append(conf)
        else:
            confs_fail.append(conf)

    fig, ax = plt.subplots(figsize=(8, 5), constrained_layout=True)
    bins = [i / 20 for i in range(21)]  # 0.0, 0.05, ..., 1.0
    ax.hist(confs_pass, bins=bins, alpha=0.7, color="#2ecc71", edgecolor="black", label=f"PASS (n={len(confs_pass)})")
    if confs_fail:
        ax.hist(confs_fail, bins=bins, alpha=0.7, color="#e74c3c", edgecolor="black", label=f"FAIL (n={len(confs_fail)})")
    ax.set_xlabel("Confidence", fontsize=11)
    ax.set_ylabel("Число предметов", fontsize=11)
    ax.set_title("Распределение confidence check_subject()", fontsize=12)
    ax.legend(loc="upper center", fontsize=9)
    ax.set_xlim(0, 1.05)
    out = OUT / "check_subject_confidence_distribution.png"
    fig.savefig(out, dpi=120)
    plt.close(fig)
    return out


def main() -> int:
    print("Генерация графиков...")
    p1 = plot_classify_confidence()
    print(f"  ✓ {p1}")
    p2 = plot_check_subject_results()
    print(f"  ✓ {p2}")
    p3 = plot_threshold_experiment()
    print(f"  ✓ {p3}")
    p4 = plot_check_subject_confusion_matrix()
    print(f"  ✓ {p4}")
    p5 = plot_check_subject_confidence_distribution()
    print(f"  ✓ {p5}")
    print("Готово.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
