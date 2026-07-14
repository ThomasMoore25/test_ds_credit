# Dockerfile для credit_check FastAPI.
#
# Сборка:
#   docker build -t credit-check:0.6.0 .
#
# Запуск:
#   docker run --rm -p 8000:8000 credit-check:0.6.0
#   # Swagger UI: http://localhost:8000/docs
#
# С LLM (опционально):
#   docker run --rm -p 8000:8000 -e OPENAI_API_KEY=sk-... credit-check:0.6.0

FROM python:3.11-slim AS base

# Системные зависимости минимальны — только то, что нужно для работы FastAPI.
# tesseract/poppler НЕ ставим — см. RESULTS.md (OCR out of scope для тестового).
LABEL org.opencontainers.image.title="credit-check"
LABEL org.opencontainers.image.version="0.6.0"
LABEL org.opencontainers.image.description="AI-агент проверки целевого использования льготных кредитов"

WORKDIR /app

# Сначала копируем только метаданные зависимостей — кэш-слой.
COPY pyproject.toml README.md ./
COPY src ./src

# Устанавливаем пакет с api extra (тащит fastapi + uvicorn).
# --no-cache-dir экономит размер образа.
RUN pip install --no-cache-dir -e ".[api]"

# Тесты в образ не копируем — он runtime-only.
EXPOSE 8000

# uvicorn с одним воркером; для production стоит gunicorn + uvicorn workers,
# но для тестового задания single-worker достаточно.
CMD ["uvicorn", "credit_check.api:app", "--host", "0.0.0.0", "--port", "8000"]
