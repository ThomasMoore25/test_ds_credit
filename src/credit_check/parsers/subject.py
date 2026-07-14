"""Парсер предмета оплаты/договора.

Извлекает короткое описание предмета из текста документа.
Используется как вход для check_subject().

Эвристики (применяются по очереди, возвращается первое успешное):
    1. Явный маркер «Предмет:» / «Предмет договора:» / «Предмет оплаты:»
    2. Шаблон договора «передать в собственность Покупателя <предмет>»
    3. Таблица с «Наименование товара» — для спецификаций и счетов
    4. Шаблон «предмет: поставка/поставка ...» (lowercase)
    5. Фоллбэк — None
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

# Шаблон «Предмет: поставка ...» (часто в счетах на услуги)
_SUBJECT_POSTAVKA_RE: Final[re.Pattern[str]] = re.compile(
    r"Предмет\s*[:\-]\s*(поставка[^\n]{5,200}|выполнение[^\n]{5,200}|оказание[^\n]{5,200})",
    re.IGNORECASE,
)

# Поиск заголовка таблицы с наименованием товара/услуги.
# Поддерживает варианты:
#   «Наименование товара», «Наименование», «Товар / Услуга», «Наименование работ»
_TABLE_HEADER_RE: Final[re.Pattern[str]] = re.compile(
    r"\|\s*№\s*\|[^|]*"
    r"(?:Наименование(?:\s+(?:товара|работ))?|Товар\s*/\s*Услуга|Товар)"
    r"[^|]*\|",
    re.IGNORECASE,
)


def _extract_from_table(text: str) -> str | None:
    """Извлекает наименование товара из ASCII-таблицы спецификации/счёта.

    Таблицы в датасете имеют вид:
        +---+----------------+---+---+
        | № | Наименование   |...|
        +---+----------------+---+---+
        | 1 | Карбамид марки Б |...|
        +---+----------------+---+---+

    Возвращает содержимое ячейки «Наименование» из первой строки данных.
    """
    # Найдём заголовок таблицы с «Наименование»
    header_match = _TABLE_HEADER_RE.search(text)
    if not header_match:
        return None

    # Возьмём текст после заголовка и поищем первую строку данных
    after_header = text[header_match.end():]
    # Пропускаем разделитель (+---+---+)
    after_header = re.sub(r"^[+\-|\s]+\n", "", after_header, count=1)

    # Ищем строку вида | 1 | <наименование> | ... |
    data_row = re.search(
        r"\|\s*\d+\s*\|\s*([^|]{3,200})\s*\|",
        after_header,
    )
    if not data_row:
        return None

    candidate = data_row.group(1).strip()
    # Схлопываем переносы и пробелы
    candidate = re.sub(r"\s+", " ", candidate)
    if len(candidate) >= 5:
        return candidate
    return None


def parse_subject(text: str) -> str | None:
    """Извлекает предмет оплаты/договора из текста.

    Возвращает короткую строку с описанием либо None.
    Переносы строк внутри предмета заменяются на пробелы.

    Приоритет:
        1. Явный маркер «Предмет:»
        2. Шаблон договора «передать в собственность»
        3. Таблица с «Наименование товара» (для spec/invoice)
        4. Шаблон «Предмет: поставка/выполнение/оказание»
        5. None
    """
    if not text:
        return None

    # 1. Явный маркер «Предмет:»
    m = _EXPLICIT_SUBJECT_RE.search(text)
    if m:
        candidate = m.group(1).strip().rstrip(".,;")
        candidate = re.split(r"\.", candidate)[0].strip()
        candidate = re.sub(r"\s+", " ", candidate)
        if len(candidate) >= 5:
            return candidate

    # 2. Шаблон поставки «передать в собственность Покупателя <предмет>»
    m = _DELIVERY_RE.search(text)
    if m:
        candidate = m.group(1).strip().rstrip(".,;")
        candidate = re.split(r",\s*в\s+лице", candidate, flags=re.IGNORECASE)[0].strip()
        candidate = re.sub(r"\s+", " ", candidate)
        if len(candidate) >= 5:
            return candidate

    # 3. Таблица с «Наименование товара» (спецификации, счета, УПД)
    table_subject = _extract_from_table(text)
    if table_subject:
        return table_subject

    # 4. Шаблон «Предмет: поставка ...» (для счетов на услуги)
    m = _SUBJECT_POSTAVKA_RE.search(text)
    if m:
        candidate = m.group(1).strip().rstrip(".,;")
        candidate = re.split(r"[\n\.]", candidate)[0].strip()
        candidate = re.sub(r"\s+", " ", candidate)
        if len(candidate) >= 5:
            return candidate

    return None
