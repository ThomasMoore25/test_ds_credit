"""LLM-модуль для check_subject().

Использует LangChain с OpenAI-совместимым API. Если переменная окружения
OPENAI_API_KEY не установлена или импорт LangChain недоступен — модуль
 gracefully возвращает None, и check_subject() переключается на keyword-fallback.

Архитектура:
    1. PromptTemplate с few-shot примерами PASS/FAIL.
    2. Output parser, ожидающий строгий JSON: {"matches": bool, "confidence": float, "reason": str}.
    3. Lightweight chain: prompt | llm | parser.
"""

from __future__ import annotations

import json
import os
import re
from typing import Any, Final

# --- Few-shot примеры ---------------------------------------------------------
# Подобраны так, чтобы покрыть основные категории датасета: агрохимия, семена,
# техника, топливо, запчасти, СЗР, страхование урожая — PASS; аренда офиса,
# юридические услуги, мебель, IT, клининг, обучение — FAIL.
_FEW_SHOT_EXAMPLES: Final[list[dict[str, str]]] = [
    {
        "subject": "Поставка минеральных удобрений (карбамид марки Б)",
        "answer": '{"matches": true, "confidence": 0.95, "reason": "минеральные удобрения относятся к категории \'агрохимия\'"}',
    },
    {
        "subject": "Поставка семян подсолнечника посевная партия 2025",
        "answer": '{"matches": true, "confidence": 0.93, "reason": "семена подсолнечника относятся к категории \'семена\'"}',
    },
    {
        "subject": "Аренда офисного помещения, г. Краснодар, ул. Ленина 15",
        "answer": '{"matches": false, "confidence": 0.95, "reason": "аренда офиса не относится к сельхоз-деятельности"}',
    },
    {
        "subject": "Юридическое сопровождение сделки, консультационные услуги",
        "answer": '{"matches": false, "confidence": 0.92, "reason": "юридические услуги не относятся к сельхоз-деятельности"}',
    },
    {
        "subject": "Техническое обслуживание и ремонт зерноуборочного комбайна John Deere",
        "answer": '{"matches": true, "confidence": 0.88, "reason": "ремонт сельхоз-техники относится к категории \'техника/запчасти/работы на полях\'"}',
    },
]

_PROMPT_TEMPLATE: Final[str] = """Ты — помощник казначейства. Определи, относится ли предмет оплаты \
к сельскохозяйственной деятельности (для льготного кредитования).

Разрешённые категории: агрохимия (удобрения, СЗР), семена и посадочный материал, \
сельхоз-техника, топливо для сельхоз-техники, запчасти к сельхоз-технике, \
корма, работы на полях (вспашка, посев, уборка, агрохимобработка), \
ветеринарные препараты, страхование урожая, агрономический консалтинг.

Не относятся: аренда офиса, юридические/консультационные услуги общего характера, \
мебель, IT-услуги, клининг, обучение (если не агро-специфика).

Ответь СТРОГО в формате JSON, без пояснений вне JSON:
{{"matches": bool, "confidence": float, "reason": str}}

Примеры:
{examples}

Предмет оплаты: {subject}
Ответ JSON:"""


def _build_examples() -> str:
    lines = []
    for ex in _FEW_SHOT_EXAMPLES:
        lines.append(f"Предмет: {ex['subject']}")
        lines.append(f"Ответ: {ex['answer']}")
        lines.append("")
    return "\n".join(lines).strip()


def _parse_llm_json(raw: str) -> dict[str, Any] | None:
    """Достаёт JSON из ответа LLM (та может добавить пояснения)."""
    # Ищем первый { ... } блок
    m = re.search(r"\{[^{}]*\}", raw, re.DOTALL)
    if not m:
        return None
    try:
        obj = json.loads(m.group(0))
    except json.JSONDecodeError:
        return None
    if not isinstance(obj, dict):
        return None
    if "matches" not in obj or "confidence" not in obj or "reason" not in obj:
        return None
    return obj


def is_llm_available() -> bool:
    """True, если LLM-движок можно использовать (есть ключ и библиотека)."""
    if not os.getenv("OPENAI_API_KEY"):
        return False
    try:
        import langchain  # noqa: F401
        import langchain_openai  # noqa: F401
    except ImportError:
        return False
    return True


def check_subject_with_llm(subject: str) -> tuple[bool, float, str] | None:
    """Вызывает LLM через LangChain.

    Returns:
        (matches, confidence, reason) или None, если LLM недоступен /
        вернула невалидный ответ.
    """
    if not is_llm_available():
        return None

    try:
        from langchain_core.prompts import PromptTemplate
        from langchain_openai import ChatOpenAI
        from langchain_core.output_parsers import StrOutputParser
    except ImportError:
        return None

    prompt = PromptTemplate.from_template(_PROMPT_TEMPLATE)
    llm = ChatOpenAI(temperature=0.0, model_name="gpt-4o-mini")
    chain = prompt | llm | StrOutputParser()

    try:
        raw = chain.invoke({"subject": subject, "examples": _build_examples()})
    except Exception:
        return None

    parsed = _parse_llm_json(str(raw))
    if not parsed:
        return None

    try:
        matches = bool(parsed["matches"])
        confidence = float(parsed["confidence"])
        reason = str(parsed["reason"])
    except (TypeError, ValueError):
        return None

    # Нормализуем confidence в [0, 1]
    confidence = max(0.0, min(1.0, confidence))
    return (matches, confidence, reason)
