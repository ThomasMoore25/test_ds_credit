"""Парсер наименования контрагента.

Распознаёт типовые формы:
    ООО «ТехАгро»
    АО «АгроСнаб»
    ПАО «Сбербанк»
    ЗАО «ТехАгро»
    ИП Смирнов В.А.
    СПК «Колос»
    КФХ «Рассвет»
    НКО «Фонд»

Возвращает строку (как в документе) либо None.
"""

from __future__ import annotations

import re
from typing import Final

# Паттерн юридического лица с кавычками «...»
# Включает СПК, КФХ, НКО — они часто встречаются в сельхоз-документах
_LEGAL_ENTITY_RE: Final[re.Pattern[str]] = re.compile(
    r"\b(ООО|АО|ПАО|ЗАО|НАО|АОЗТ|ТОО|ОАО|СПК|КФХ|НКО)\s+"
    r"[«\"„]\s*([^»\"“]{1,80})\s*[»\"“]",
)

# Паттерн ИП: «ИП Фамилия И.О.»
_IP_RE: Final[re.Pattern[str]] = re.compile(
    r"\bИП\s+([А-ЯЁ][а-яё]+(?:\s+[А-ЯЁ][а-яё]+)*\s+[А-ЯЁ]\.[А-ЯЁ]\.)",
)


def parse_contractor(text: str) -> str | None:
    """Извлекает контрагента из текста.

    Возвращает строку вида 'ООО «ТехАгро»', 'ИП Смирнов В.А.',
    'СПК «Колос»' или 'КФХ «Рассвет»' либо None.
    Если в тексте несколько контрагентов — возвращается первый встретившийся.
    """
    if not text:
        return None

    # 1. Юрлица (включая СПК, КФХ, НКО)
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


def parse_contractor_extended(text: str) -> str | None:
    """Извлекает контрагента с поддержкой СПК, КФХ, НКО.

    Deprecated: используйте parse_contractor — он теперь поддерживает все формы.
    Функция оставлена для обратной совместимости.
    """
    return parse_contractor(text)
