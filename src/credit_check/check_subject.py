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

import re
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
            "рассад", "саженц", "гибрид", "сорт ", "элита", "репродукция", "клубни", "луковиц",
        ),
        description="семена и посадочный материал",
    ),
    _Category(
        name="техника",
        keywords=(
            "трактор", "комбайн", "зерноуборочн", "сеялк", "плуг", "борон",
            "культиватор", "опрыскиват", "сельхозтехник", "сельхоз-техник",
            "с/х техник", "john deere", "мтз", "к-7", "лемкен",
            "new holland", "case ih", "claas", "rostselmash", "агромаш", "вектор",
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
            "концентрат", "премикс", "бвмд", "стартер", "дрожжи кормовые", "патока кормовая",
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
# v0.3.0: расширено для устранения ложных срабатываний на EDGE-кейсах
# («уборка административного здания» fuzzy-матчится с «уборк» из категории
# «работы на полях»). Запрещённые слова имеют ПРИОРИТЕТ над разрешёнными —
# это безопаснее для казначейства (лучше пропустить к ручной проверке, чем
# одобрить нецелевой платёж).
_FORBIDDEN_KEYWORDS: Final[tuple[str, ...]] = (
    # Недвижимость и офисная деятельность
    "офис", "аренд офис", "помещени", "канцеляр", "мебел",
    # IT и маркетинг
    "seo", "сайт", "разработка", "продвижение", "реклам",
    # Юридические и консультационные услуги
    "юридическ", "консультационн", "консультаци",
    # Обучение
    "обучени", "курсы", "тренинг", "семинар",
    # Клининг и бытовые услуги
    "клининг", "уборк административн", "уборк здания", "уборк помещени",
    # Финансовые и бухгалтерские услуги
    "бухгалтерск", "аудит", "налогов",
    # Логистика общего назначения (не сельхоз-доставка)
    "перевозк грузов", "экспедир",
    # Медицина общая (не ветеринария)
    "медицинск", "стоматолог",
)

# Сильные запрещённые слова — однозначный отказ даже при наличии сельхоз-признака.
# Это «убийцы» ложных срабатываний: если в предмете есть хотя бы одно из них,
# возвращаем FAIL с высокой уверенностью, игнорируя любые совпадения с разрешёнными.
_STRONG_FORBIDDEN: Final[tuple[str, ...]] = (
    "офисн",
    "административн",
    "клининг",
    "юридическ",
    "консультационн",
    "seo",
    "обучени",
    "мебел",
    "канцеляр",
    "бухгалтерск",
    "аудит",
)

# v0.4.0: Сильные сельхоз-контекстные слова — перебивают STRONG_FORBIDDEN.
# Если в предмете есть хотя бы одно из них, то запрещённые слова вроде
# «консультационн» НЕ вызывают однозначный отказ. Это исправляет EDGE-кейс
# «услуги агронома-консультанта» — агрономическая консультация относится
# к сельхоз-деятельности, а не к общим консультационным услугам.
_STRONG_AGRI_CONTEXT: Final[tuple[str, ...]] = (
    "агроном",
    "агрохимик",
    "агроинженер",
    "ветеринар",
    "зоотехник",
    "фермерск",
    "сельхоз",
    "сельск хозя",
    "полевод",
    "животновод",
    "растениевод",
    "семеновод",
    "почвовед",
    "агролес",
    "мелиорат",
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


def _find_matched_word(subject: str, keyword: str) -> str:
    """Находит слово в subject, содержащее keyword (для человекочитаемого reason).

    Например: subject='Поставка минеральных удобрений', keyword='удобр'
    → возвращает 'удобрений'. Если точного вхождения нет — возвращает keyword
    без последней буквы-основы (для 'офисн' → 'офис'), чтобы reason был читаемым.
    """
    s_lower = subject.lower()
    if keyword in s_lower:
        # Ищем слово, содержащее keyword
        for word in re.split(r"[^\w-]+", s_lower):
            if keyword in word and len(word) >= len(keyword):
                return word
    # Точного вхождения нет (fuzzy match). Возвращаем keyword без последней
    # буквы-основы, чтобы получить читаемую форму: 'офисн' → 'офис',
    # 'юридическ' → 'юридичес', 'административн' → 'административ'.
    if len(keyword) > 4 and keyword[-1] in "нкия":
        return keyword[:-1]
    return keyword


def _fallback_check(subject: str) -> tuple[bool, float, str]:
    """Keyword + fuzzy matching fallback. Всегда доступен без API ключей.

    v0.3.0: если в предмете есть СИЛЬНОЕ запрещённое слово — однозначный FAIL
    с высокой уверенностью, даже если есть совпадение с разрешённой категорией.
    Это устраняет ложные PASS на EDGE-кейсах типа «уборка административного здания».

    v0.4.0: если есть СИЛЬНОЕ сельхоз-контекстное слово (агроном, ветеринар, и т.п.),
    то STRONG_FORBIDDEN не срабатывает — это исправляет EDGE-кейс «агроном-консультант».
    """
    s = subject.lower().strip()

    if not s:
        return (False, 0.5, "пустой предмет оплаты")

    # 1. Проверяем СИЛЬНЫЕ сельхоз-контекстные слова — они перебивают запрещённые
    agri_context_hits = [kw for kw in _STRONG_AGRI_CONTEXT if _match_keyword(s, kw)]

    # 2. СИЛЬНЫЕ запрещённые — срабатывают, только если НЕТ agri_context
    if not agri_context_hits:
        strong_forbidden_hits = [kw for kw in _STRONG_FORBIDDEN if _match_keyword(s, kw)]
        if strong_forbidden_hits:
            kw = strong_forbidden_hits[0]
            word = _find_matched_word(subject, kw)
            return (
                False,
                0.92,
                f"{word} не относится к сельхоз-деятельности",
            )

    # 2. Общие запрещённые
    forbidden_hits = [kw for kw in _FORBIDDEN_KEYWORDS if _match_keyword(s, kw)]

    # 3. Разрешённые категории
    matched_categories: list[_Category] = []
    matched_keyword_for_cat: dict[str, str] = {}  # cat.name → конкретное слово из subject
    for cat in _ALLOWED_CATEGORIES:
        for kw in cat.keywords:
            if _match_keyword(s, kw):
                matched_categories.append(cat)
                # Находим конкретное слово из subject для человекочитаемого reason
                matched_keyword_for_cat[cat.name] = _find_matched_word(subject, kw)
                break

    if matched_categories and not forbidden_hits:
        cat = matched_categories[0]
        word = matched_keyword_for_cat[cat.name]
        # Уверенность зависит от числа совпавших категорий (1 = 0.85, ≥2 = 0.92)
        confidence = 0.92 if len(matched_categories) >= 2 else 0.85
        return (True, confidence, f"{word} относится к категории '{cat.name}'")

    # v0.4.0: если есть agri_context (агроном, ветеринар, и т.п.) — это PASS,
    # даже если ни одна категория не сматчилась и даже если есть forbidden_hits.
    # Агроном-консультант — это сельхоз-деятельность, не «консультационные услуги».
    if agri_context_hits:
        kw = agri_context_hits[0]
        return (
            True,
            0.85,
            f"предмет относится к сельхоз-деятельности (контекст: '{kw}')",
        )

    if forbidden_hits and not matched_categories:
        kw = forbidden_hits[0]
        word = _find_matched_word(subject, kw)
        return (False, 0.91, f"{word} не относится к сельхоз-деятельности")

    if forbidden_hits and matched_categories:
        # Смешанный случай — теперь это редкость (сильные запрещённые отрабатывают раньше).
        # Снижаем уверенность и отправляем на ручную проверку.
        return (
            False,
            0.6,
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
        >>> check_subject("Поставка минеральных удобрений")
        (True, 0.85, "удобрений относится к категории 'агрохимия'")
        >>> check_subject("Аренда офисного помещения")
        (False, 0.92, "офисного не относится к сельхоз-деятельности")
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
