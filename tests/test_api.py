"""Тесты для FastAPI-обёртки (credit_check.api).

Запускается через TestClient из FastAPI — реальный сервер не поднимается.
"""

from __future__ import annotations

import pytest

pytest.importorskip("fastapi")
pytest.importorskip("httpx")

from fastapi.testclient import TestClient  # noqa: E402

from credit_check.api import app  # noqa: E402

client = TestClient(app)


def test_health() -> None:
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["version"] == "0.3.0"


def test_extract_endpoint_basic() -> None:
    response = client.post(
        "/extract",
        json={"text": "Сумма: 1 250 000,00 руб. ИНН 7701234567"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["amount"] == 1_250_000.0
    assert data["inn"] == "7701234567"
    assert data["date"] is None
    assert data["contractor"] is None


def test_extract_endpoint_empty_text_rejected() -> None:
    """Пустой текст не должен проходить валидацию (min_length=1)."""
    response = client.post("/extract", json={"text": ""})
    assert response.status_code == 422  # Unprocessable Entity


def test_classify_endpoint_invoice() -> None:
    text = "СЧЁТ НА ОПЛАТУ № 12 от 03.03.2025. Поставщик: ООО «Ромашка»"
    response = client.post("/classify", json={"text": text})
    assert response.status_code == 200
    data = response.json()
    assert data["doc_type"] == "invoice"
    assert data["confidence"] > 0.5


def test_classify_endpoint_unknown() -> None:
    response = client.post("/classify", json={"text": "случайный текст без маркеров"})
    assert response.status_code == 200
    assert response.json()["doc_type"] == "unknown"


def test_check_subject_endpoint_pass() -> None:
    response = client.post(
        "/check-subject",
        json={"subject": "Поставка минеральных удобрений (карбамид марки Б)"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["matches"] is True
    assert 0.0 <= data["confidence"] <= 1.0
    assert isinstance(data["reason"], str)


def test_check_subject_endpoint_fail() -> None:
    response = client.post(
        "/check-subject",
        json={"subject": "Аренда офисного помещения в Краснодаре"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["matches"] is False


def test_pipeline_endpoint_full() -> None:
    """Pipeline должен вернуть extract + classify + check_subject (если subject есть)."""
    text = (
        "ДОГОВОР ПОСТАВКИ № 47/2025 от 01.03.2025\n"
        "ООО «ТехАгро», ИНН 7701234567\n"
        "Поставщик обязуется передать в собственность Покупателя "
        "минеральные удобрения (карбамид марки Б), а Покупатель обязуется принять.\n"
        "Сумма договора: 1 250 000,00 руб."
    )
    response = client.post("/pipeline", json={"text": text})
    assert response.status_code == 200
    data = response.json()
    assert data["extract"]["amount"] == 1_250_000.0
    assert data["extract"]["inn"] == "7701234567"
    assert data["extract"]["contractor"] == "ООО «ТехАгро»"
    assert data["classify"]["doc_type"] == "contract"
    # subject извлечён → check_subject должен отработать
    assert data["check_subject"] is not None
    assert data["check_subject"]["matches"] is True


def test_pipeline_endpoint_no_subject() -> None:
    """Если subject не извлечён — check_subject должен быть None."""
    text = "СЧЁТ НА ОПЛАТУ № 12 от 03.03.2025. Поставщик: ООО «Ромашка»"
    response = client.post("/pipeline", json={"text": text})
    assert response.status_code == 200
    data = response.json()
    assert data["check_subject"] is None


def test_openapi_docs_available() -> None:
    """Swagger UI должен быть доступен."""
    response = client.get("/docs")
    assert response.status_code == 200


def test_openapi_schema_available() -> None:
    """OpenAPI схема должна быть доступна."""
    response = client.get("/openapi.json")
    assert response.status_code == 200
    schema = response.json()
    assert schema["info"]["title"] == "Credit Check API"
    # Пути в OpenAPI хранятся с ведущим '/'
    paths = schema["paths"]
    assert "/extract" in paths
    assert "/classify" in paths
    assert "/check-subject" in paths
    assert "/pipeline" in paths
    assert "/health" in paths
