"""classify(text: str) -> tuple[str, float] — классификация типа документа.

Подход: взвешенный keyword scoring.
    1. Для каждого класса (contract, spec, invoice, act) задан набор
       маркеров с весами, отражающими их «типичность».
    2. Считаем суммарный скор по каждому классу, нормируем через softmax
       в диапазон [0, 1] — это и есть уверенность.
    3. Если разрыв между скором топ-1 и топ-2 меньше порога — возвращаем
       unknown (это защищает от ненадёжных ответов на OCR-мусоре и
       коротких/обрывочных текстах).

Порог MARGIN_THRESHOLD = 0.15 подобран эмпирически на датасете из 6 файлов.
Обоснование — см. RESULTS.md.
"""

from __future__ import annotations

import math
import re
from typing import Final

# --- Классы -------------------------------------------------------------------

DocType = str  # 'contract' | 'spec' | 'invoice' | 'act' | 'unknown'

VALID_TYPES: Final[tuple[str, ...]] = ("contract", "spec", "invoice", "act", "unknown")

# --- Маркеры классов ----------------------------------------------------------
# Веса подобраны эмпирически: сильные «сигнальные» слова — 3.0, типичные — 2.0,
# косвенные — 1.0. Порядок маркеров не важен.
_MARKERS: Final[dict[str, dict[str, float]]] = {
    "contract": {
        r"\bдоговор\b": 3.0,
        r"\bдоговора\b": 2.0,
        r"\bпредмет\s+договора\b": 3.0,
        r"\bпоставщик\b": 2.0,
        r"\bпокупатель\b": 2.0,
        r"\bсумма\s+договора\b": 3.0,
        r"\bсроки\s+и\s+условия\b": 2.5,
        r"\bподписи\s+сторон\b": 2.0,
        r"\bпредмет\s+договора\b": 3.0,
        r"\bобязуется\s+передать\s+в\s+собственность\b": 3.0,
        r"\bнастоящего\s+договора\b": 2.0,
    },
    "spec": {
        r"\bспецификация\b": 3.5,
        r"\bк\s+договору\b": 2.0,
        r"\bнаименование\s+товара\b": 2.0,
        r"\bноменклатура\b": 1.5,
        r"\bед\.?\b": 0.5,
        r"\bкол-во\b": 1.0,
        r"\bцена[,\s]+руб": 1.5,
        r"\bсумма[,\s]+руб": 1.5,
        r"\bитего\s+без\s+ндс\b": 3.0,
        r"\bитого\s+с\s+ндс\b": 3.0,
        r"\bдата\s+составления\b": 2.0,
        r"\bусловия\s+поставки\b": 1.5,
    },
    "invoice": {
        r"\bсч[её]т\s+на\s+оплату\b": 3.5,
        r"\bсч[её]т\s*№\s*\d": 2.5,
        r"\bсч[её]т-фактура\b": 2.5,
        r"\bоснование\s*:?\s*договор": 1.5,
        r"\bсрок\s+оплаты\b": 2.0,
        r"\bоплата\s+до\b": 2.0,
        r"\bбик\b": 1.5,
        r"\bр/с\b": 1.5,
        r"\bк/с\b": 1.0,
        r"\bвсего\s+наименований\b": 2.5,
        r"\bглавный\s+бухгалтер\b": 2.0,
        r"\bтот\s+на\s+сумму\b": 1.5,
    },
    "act": {
        r"\bакт\s+выполненных\s+работ\b": 3.5,
        r"\bакт\b(?!\s+выполненных)": 1.0,
        r"\bупд\b": 3.5,
        r"\bуниверсальный\s+передаточный\s+документ\b": 3.5,
        r"\bработ[ыа]\s+выполнены\b": 2.5,
        r"\bтовар\s+передан\b": 2.0,
        r"\bтовар\s+получен\b": 2.0,
        r"\bработы\s+приняты\b": 2.5,
        r"\bоснование\s+передачи\b": 2.0,
        r"\bстатус\s+документа\b": 1.5,
        r"\bпретензий\s+по\s+качеству\b": 2.0,
        r"\bндс\s+не\s+облагается\b": 1.5,
    },
}

# Порог разрыва топ-1/топ-2 в абсолютных значениях softmax-вероятностей.
# Подобран на датасете (см. RESULTS.md).
MARGIN_THRESHOLD: Final[float] = 0.15

# Минимальный абсолютный скор топ-1 — если все скоры крошечные,
# документ не похож ни на один из классов.
MIN_TOP1_SCORE: Final[float] = 2.0


def _score_class(text: str, patterns: dict[str, float]) -> float:
    """Сумма весов совпавших маркеров для класса."""
    text_lower = text.lower()
    score = 0.0
    for pat, weight in patterns.items():
        if re.search(pat, text_lower):
            score += weight
    return score


def _softmax(scores: dict[str, float]) -> dict[str, float]:
    """Softmax по скорам классов. Возвращает вероятности в [0, 1]."""
    if not scores:
        return {}
    max_score = max(scores.values())
    if max_score == 0:
        # Все скоры нулевые — равномерное распределение
        n = len(scores)
        return {k: 1.0 / n for k in scores}
    exps = {k: math.exp(v - max_score) for k, v in scores.items()}
    total = sum(exps.values())
    return {k: v / total for k, v in exps.items()}


def classify(text: str) -> tuple[str, float]:
    """Классифицирует тип документа по содержимому.

    Args:
        text: текст документа.

    Returns:
        Кортеж (doc_type, confidence), где
            doc_type    — один из 'contract', 'spec', 'invoice', 'act', 'unknown'
            confidence  — уверенность в ответе в диапазоне [0, 1]

    Если разрыв между топ-1 и топ-2 меньше MARGIN_THRESHOLD или скор топ-1
    ниже MIN_TOP1_SCORE — возвращается ('unknown', confidence_топ-1).

    Examples:
        >>> doc_type, confidence = classify("Счёт на оплату №12 от 01.03.2025 ...")
        >>> doc_type
        'invoice'
        >>> confidence > 0.5
        True
    """
    if not isinstance(text, str):
        raise TypeError(f"text must be str, got {type(text).__name__}")

    if not text.strip():
        return ("unknown", 0.0)

    raw_scores = {cls: _score_class(text, pats) for cls, pats in _MARKERS.items()}
    probs = _softmax(raw_scores)

    # Сортируем по убыванию вероятности
    ranked = sorted(probs.items(), key=lambda kv: kv[1], reverse=True)
    top1_cls, top1_prob = ranked[0]
    top2_prob = ranked[1][1] if len(ranked) > 1 else 0.0

    # Условие unknown: низкий абсолютный скор или малый разрыв
    if raw_scores[top1_cls] < MIN_TOP1_SCORE:
        return ("unknown", top1_prob)
    if (top1_prob - top2_prob) < MARGIN_THRESHOLD:
        return ("unknown", top1_prob)

    return (top1_cls, top1_prob)
