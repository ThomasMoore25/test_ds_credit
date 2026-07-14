# Security Policy

## Supported Versions

Только последняя версия (0.6.x) получает security-обновления.

## Reporting a Vulnerability

Если вы нашли уязвимость, **не создавайте public issue**.
Напишите на email (указан в профиле GitHub) с описанием:

1. Шаги для воспроизведения
2. Влияние (что может сделать атакующий)
3. Возможные пути исправления (если есть)

Ответ в течение 72 часов. После исправления — публичное упоминание (если хотите).

## Known Security Considerations

1. **FastAPI без аутентификации** — текущая реализация не защищена.
   Не деплоить в production без добавления API key / JWT.
2. **OPENAI_API_KEY в env** — не логировать. `.env` в `.gitignore`.
3. **LLM output validation** — `check_subject_with_llm` парсит JSON из ответа LLM,
   но не выполняет sanitization. Если LLM вернёт вредоносный JSON —
   fallback на keyword matching.
4. **OCR-мусор** — парсеры отбрасывают невалидные данные (например, ИНН с буквами).
   Это сознательное решение для безопасности казначейства.
