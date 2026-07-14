"""FastAPI-обёртка над пайплайном credit_check.

Эндпоинты:
    POST /extract         — извлечение полей из текста
    POST /classify        — классификация типа документа
    POST /check-subject   — проверка предмета оплаты
    POST /pipeline        — полный пайплайн (extract + classify + check_subject)
    GET  /health          — health-check

Запуск:
    pip install -e ".[api]"
    uvicorn credit_check.api:app --reload --port 8000

Пример:
    curl -X POST http://localhost:8000/extract \
        -H "Content-Type: application/json" \
        -d '{"text": "Сумма: 1 250 000,00 руб. ИНН 7701234567"}'
"""

from __future__ import annotations

from typing import Optional

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from credit_check import check_subject, classify, extract

app = FastAPI(
    title="Credit Check API",
    description="AI-агент проверки целевого использования льготных кредитов",
    version="0.7.0",
)


# --- Модели запросов/ответов --------------------------------------------------


class TextRequest(BaseModel):
    """Запрос с текстом документа."""
    text: str = Field(..., min_length=1, max_length=100_000, description="Текст документа")


class SubjectRequest(BaseModel):
    """Запрос с предметом оплаты."""
    subject: str = Field(..., min_length=1, max_length=10_000, description="Предмет оплаты")


class ExtractResponse(BaseModel):
    """Ответ extract()."""
    amount: Optional[float] = None
    date: Optional[str] = None
    inn: Optional[str] = None
    contractor: Optional[str] = None
    subject: Optional[str] = None


class ClassifyResponse(BaseModel):
    """Ответ classify()."""
    doc_type: str
    confidence: float


class CheckSubjectResponse(BaseModel):
    """Ответ check_subject()."""
    matches: bool
    confidence: float
    reason: str


class PipelineResponse(BaseModel):
    """Комбинированный ответ полного пайплайна."""
    extract: ExtractResponse
    classify: ClassifyResponse
    check_subject: Optional[CheckSubjectResponse] = None


class HealthResponse(BaseModel):
    """Health-check ответ."""
    status: str = "ok"
    version: str = "0.7.0"


class VersionResponse(BaseModel):
    """Ответ /version."""
    version: str
    python_version: str
    api_title: str


# --- Эндпоинты -----------------------------------------------------------------


@app.get("/health", response_model=HealthResponse, tags=["meta"])
def health() -> HealthResponse:
    """Health-check."""
    return HealthResponse()


@app.get("/version", response_model=VersionResponse, tags=["meta"])
def version() -> VersionResponse:
    """Возвращает версию API и Python."""
    import sys
    from credit_check import __version__
    return VersionResponse(
        version=__version__,
        python_version=f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
        api_title=app.title,
    )


@app.post("/extract", response_model=ExtractResponse, tags=["pipeline"])
def extract_endpoint(req: TextRequest) -> ExtractResponse:
    """Извлекает поля из текста документа."""
    try:
        result = extract(req.text)
    except TypeError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return ExtractResponse(**result)


@app.post("/classify", response_model=ClassifyResponse, tags=["pipeline"])
def classify_endpoint(req: TextRequest) -> ClassifyResponse:
    """Классифицирует тип документа."""
    try:
        doc_type, confidence = classify(req.text)
    except TypeError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return ClassifyResponse(doc_type=doc_type, confidence=confidence)


@app.post("/check-subject", response_model=CheckSubjectResponse, tags=["pipeline"])
def check_subject_endpoint(req: SubjectRequest) -> CheckSubjectResponse:
    """Проверяет, подходит ли предмет оплаты под льготную программу."""
    try:
        matches, confidence, reason = check_subject(req.subject)
    except TypeError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return CheckSubjectResponse(matches=matches, confidence=confidence, reason=reason)


@app.post("/pipeline", response_model=PipelineResponse, tags=["pipeline"])
def pipeline_endpoint(req: TextRequest) -> PipelineResponse:
    """Полный пайплайн: extract + classify + check_subject (если subject найден)."""
    try:
        result = extract(req.text)
        doc_type, confidence = classify(req.text)
    except TypeError as e:
        raise HTTPException(status_code=400, detail=str(e))

    check_result = None
    if result.get("subject"):
        try:
            matches, conf, reason = check_subject(result["subject"])
            check_result = CheckSubjectResponse(
                matches=matches, confidence=conf, reason=reason
            )
        except TypeError:
            check_result = None

    return PipelineResponse(
        extract=ExtractResponse(**result),
        classify=ClassifyResponse(doc_type=doc_type, confidence=confidence),
        check_subject=check_result,
    )
