"""check_subject(subject: str) -> tuple[bool, float, str] — проверка предмета оплаты.

Возвращает:
    matches     — True, если предмет подходит под льготную программу
    confidence  — уверенность в [0, 1]
    reason      — человекочитаемое объяснение

Два движка:
    1. LLM через LangChain (если есть OPENAI_API_KEY и установлена langchain).
    2. Fallback на keyword matching + rapidfuzz (всегда доступен).

Для казначейства критично, чтобы код запускался локально без ключей — поэтому
fallback обязателен и используется по умолчанию, если LLM недоступен.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Final

from rapidfuzz import fuzz

from credit_check.llm import check_subject_with_llm, is_llm_available

# --- Разрешённые категории ----------------------------------------------------


@dataclass(frozen=True)
class _Category:
    name: str
    keywords: tuple[str, ...]
    description: str


_ALLOWED_CATEGORIES: Final[tuple[_Category, ...]] = (
    _Category(
        name="агрохимия",
        keywords=(
            "удобр", "карбамид", "аммиачн", "кас-32", "кас 32", "кас32",
            "нитроаммофос", "азофос", "комплексн",
            "гербицид", "фунгицид", "инсектицид", "пестицид",
            "средств защиты растений", "сзр", "агрохим",
        ),
        description="удобрения и средства защиты растений (агрохимия)",
    ),
    _Category(
        name="семена",
        keywords=(
            "семян", "семена", "посевная партия", "посадочный материал",
            "рассад", "саженц", "гибрид", "сорт ",
        ),
        description="семена и посадочный материал",
    ),
    _Category(
        name="техника",
        keywords=(
            "трактор", "комбайн", "зерноуборочн", "сеялк", "плуг", "борон",
            "культиватор", "опрыскиват", "сельхозтехник", "сельхоз-техник",
            "с/х техник", "john deere", "мтз", "к-7", "лемкен",
        ),
        description="сельскохозяйственная техника",
    ),
    _Category(
        name="топливо",
        keywords=(
            "дизельн", "бензин", "топлив", "солярк", "гсм", "газ моторн",
            "пропан-бутан", "сжиженный газ",
        ),
        description="топливо для сельхоз-техники",
    ),
    _Category(
        name="запчасти",
        keywords=(
            "запчаст", "запасных частей", "детал", "ремонт сельхоз",
            "ремонт комбайн", "ремонт трактор", "техническое обслуживание",
            "то трактор", "то комбайн",
        ),
        description="запчасти и ТО/ремонт сельхоз-техники",
    ),
    _Category(
        name="корма",
        keywords=(
            "корм", "комбикорм", "сено", "силос", "сенаж", "солома",
            "концентрат", "премикс",
        ),
        description="корма для животных",
    ),
    _Category(
        name="работы на полях",
        keywords=(
            "вспашк", "бороновани", "посев", "уборк", "внесени",
            "агрохимическ", "агрохимработ", "обработка почв",
            "предпосевн", "почвенный анализ", "агрономическ",
            "работы на полях", "полевые работы",
        ),
        description="агрохимические и полевые работы",
    ),
    _Category(
        name="ветеринарные препараты",
        keywords=(
            "ветеринар", "ветпрепарат", "вакцин", "антибиотик для животн",
            "дезинфекци",
        ),
        description="ветеринарные препараты",
    ),
    _Category(
        name="страхование урожая",
        keywords=(
            "страхован", "урожай", "посевов",
        ),
        description="страхование урожая и посевов",
    ),
)

# Категории, которые ЯВНО не относятся к сельскому хозяйству.
# Используются для повышения уверенности в отказе.
_FORBIDDEN_KEYWORDS: Final[tuple[str, ...]] = (
    "офис", "аренд офис", "канцеляр", "мебел", "клининг", "уборк административн",
    "seo", "сайт", "разработка", "продвижение", "юридическ", "консультационн",
    "обучени", "курсы", "тренинг",
)

# Порог fuzzy-совпадения для keyword matching
_FUZZY_THRESHOLD: Final[int] = 80  # 0..100, partial_ratio


def _match_keyword(subject_lower: str, keyword: str) -> bool:
    """True, если keyword найден в subject (точно или fuzzy)."""
    if keyword in subject_lower:
        return True
    # Fuzzy — для опечаток и словоформ
    score = fuzz.partial_ratio(keyword, subject_lower)
    return score >= _FUZZY_THRESHOLD


def _fallback_check(subject: str) -> tuple[bool, float, str]:
    """Keyword + fuzzy matching fallback. Всегда доступен без API ключей."""
    s = subject.lower().strip()

    if not s:
        return (False, 0.5, "пустой предмет оплаты")

    # 1. Проверяем запрещённые категории
    forbidden_hits = [kw for kw in _FORBIDDEN_KEYWORDS if _match_keyword(s, kw)]

    # 2. Проверяем разрешённые категории
    matched_categories: list[_Category] = []
    for cat in _ALLOWED_CATEGORIES:
        for kw in cat.keywords:
            if _match_keyword(s, kw):
                matched_categories.append(cat)
                break

    if matched_categories and not forbidden_hits:
        cat = matched_categories[0]
        # Уверенность зависит от числа совпавших категорий (1 = 0.85, ≥2 = 0.92)
        confidence = 0.92 if len(matched_categories) >= 2 else 0.85
        return (True, confidence, f"предмет относится к категории '{cat.name}'")

    if forbidden_hits and not matched_categories:
        kw = forbidden_hits[0]
        return (False, 0.91, f"предмет содержит признак не-сельхоз-деятельности ('{kw}')")

    if forbidden_hits and matched_categories:
        # Смешанный случай — снижаем уверенность
        return (
            False,
            0.55,
            "предмет содержит и сельхоз-, и не-сельхоз-признаки — требуется ручная проверка",
        )

    # Ничего не найдено
    return (
        False,
        0.5,
        "не найдено совпадений с разрешёнными сельхоз-категориями",
    )


def check_subject(subject: str) -> tuple[bool, float, str]:
    """Определяет, подходит ли предмет оплаты под льготную сельхоз-программу.

    Args:
        subject: предмет оплаты (строка из документа или введённая пользователем).

    Returns:
        Кортеж (matches, confidence, reason):
            matches     — bool, True если предмет подходит
            confidence  — float в [0, 1]
            reason      — человекочитаемое объяснение

    Стратегия:
        1. Если доступен LLM (OPENAI_API_KEY + langchain) — используется LLM
           через LangChain.
        2. Иначе — keyword + fuzzy matching по словарю категорий.
        3. Если LLM вернул невалидный ответ — fallback на keyword.

    Examples:
        >>> check_subject("удобрения карбамид")
        (True, 0.85, "предмет относится к категории 'агрохимия'")
        >>> check_subject("аренда офиса")
        (False, 0.91, "предмет содержит признак не-сельхоз-деятельности ('офис')")
    """
    if not isinstance(subject, str):
        raise TypeError(f"subject must be str, got {type(subject).__name__}")

    # 1. Пробуем LLM
    if is_llm_available():
        llm_result = check_subject_with_llm(subject)
        if llm_result is not None:
            return llm_result

    # 2. Fallback
    return _fallback_check(subject)
