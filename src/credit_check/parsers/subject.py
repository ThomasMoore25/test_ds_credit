"""Парсер предмета оплаты/договора.

Извлекает короткое описание предмета из текста документа.
Используется как вход для check_subject().

Эвристики:
    1. Поиск секции «Предмет:» / «Предмет договора:» / «Предмет оплаты:»
    2. Поиск шаблона «Поставщик обязуется передать ... <предмет>»
    3. Фоллбэк — None
"""

from __future__ import annotations

import re
from typing import Final

# Явный маркер «Предмет: ...»
_EXPLICIT_SUBJECT_RE: Final[re.Pattern[str]] = re.compile(
    r"Предмет\s*(?:договора|оплаты)?\s*[:\-]\s*"
    r"([^\n]{5,200})",
    re.IGNORECASE,
)

# Шаблон договора: «передать в собственность Покупателя <предмет>»
_DELIVERY_RE: Final[re.Pattern[str]] = re.compile(
    r"передать\s+в\s+собственность\s+Покупателя\s+(.{5,300}?)(?:,\s*а\s+Покупатель|\.|$)",
    re.IGNORECASE | re.DOTALL,
)

# «Стоимость услуг составляет ...» — для случаев, где предмет — услуга
# (не извлекает предмет напрямую, но сигнализирует, что нужно искать выше)


def parse_subject(text: str) -> str | None:
    """Извлекает предмет оплаты/договора из текста.

    Возвращает короткую строку с описанием либо None.
    Переносы строк внутри предмета заменяются на пробелы.
    """
    if not text:
        return None

    # 1. Явный маркер
    m = _EXPLICIT_SUBJECT_RE.search(text)
    if m:
        candidate = m.group(1).strip().rstrip(".,;")
        # Ограничиваем длину — берём до первой точки
        candidate = re.split(r"\.", candidate)[0].strip()
        # Схлопываем переносы строк и лишние пробелы
        candidate = re.sub(r"\s+", " ", candidate)
        if len(candidate) >= 5:
            return candidate

    # 2. Шаблон поставки
    m = _DELIVERY_RE.search(text)
    if m:
        candidate = m.group(1).strip().rstrip(".,;")
        # Убираем фразы типа «в лице...»
        candidate = re.split(r",\s*в\s+лице", candidate, flags=re.IGNORECASE)[0].strip()
        # Схлопываем переносы строк и лишние пробелы
        candidate = re.sub(r"\s+", " ", candidate)
        if len(candidate) >= 5:
            return candidate

    return None
