"""Парсер наименования контрагента.

Распознаёт типовые формы:
    ООО «ТехАгро»
    АО «АгроСнаб»
    ПАО «Сбербанк»
    ЗАО «ТехАгро»
    ИП Смирнов В.А.
    ИП Иванов И.И.

Возвращает строку (как в документе) либо None.
"""

from __future__ import annotations

import re
from typing import Final

# Паттерн юридического лица с кавычками «...»
_LEGAL_ENTITY_RE: Final[re.Pattern[str]] = re.compile(
    r"\b(ООО|АО|ПАО|ЗАО|НАО|АОЗТ|ТОО|ОАО)\s+"
    r"[«\"„]\s*([^»\"“]{1,80})\s*[»\"“]",
)

# Паттерн ИП: «ИП Фамилия И.О.»
_IP_RE: Final[re.Pattern[str]] = re.compile(
    r"\bИП\s+([А-ЯЁ][а-яё]+(?:\s+[А-ЯЁ][а-яё]+)*\s+[А-ЯЁ]\.[А-ЯЁ]\.)",
)


def parse_contractor(text: str) -> str | None:
    """Извлекает контрагента из текста.

    Возвращает строку вида 'ООО «ТехАгро»' или 'ИП Смирнов В.А.' либо None.
    Если в тексте несколько контрагентов — возвращается первый встретившийся.
    """
    if not text:
        return None

    # 1. Юрлица
    m = _LEGAL_ENTITY_RE.search(text)
    if m:
        form = m.group(1)
        name = m.group(2).strip()
        return f"{form} «{name}»"

    # 2. ИП
    m = _IP_RE.search(text)
    if m:
        return f"ИП {m.group(1).strip()}"

    return None


# Дополнительные формы (СПК, КФХ) — расширение
_SPK_RE = __import__('re').compile(
    r"\b(СПК|КФХ|НКО)\s+[«\"„]([^»\"“]{1,80})[»\"“]",
    __import__('re').IGNORECASE,
)


def parse_contractor_extended(text: str) -> str | None:
    """Извлекает контрагента с поддержкой СПК, КФХ, НКО."""
    if not text:
        return None
    m = _SPK_RE.search(text)
    if m:
        return f"{m.group(1)} «{m.group(2).strip()}»"
    return None
