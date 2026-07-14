# Contributing

Спасибо за интерес к проекту! Этот файл описывает, как вносить изменения.

## Разработка

```bash
# Клонировать и установить
git clone https://github.com/ThomasMoore25/test_ds_credit.git
cd test_ds_credit
pip install -e ".[dev,api]"

# Запустить тесты
pytest

# Сгенерировать графики
python scripts/generate_plots.py
```

## Правила

1. **Код**: type hints, docstrings, PEP8. Без «магических чисел» — выносить в константы.
2. **Тесты**: каждое новое поведение должно покрываться тестом. Минимум — happy path + 1 edge case.
3. **Коммиты**: префикс `feat:` / `fix:` / `docs:` / `test:` / `refactor:`.
4. **Датасет**: не модифицировать файлы в `dataset/` — они предоставлены заказчиком.
5. **Версии**: обновлять `__version__` в `src/credit_check/__init__.py` и `pyproject.toml` одновременно.

## Структура

- `src/credit_check/` — основной код
- `src/credit_check/parsers/` — парсеры полей
- `src/credit_check/llm/` — LLM-обёртки (опционально)
- `tests/` — тесты pytest
- `scripts/` — утилиты (генерация графиков и т.п.)
- `docs/images/` — PNG-графики

## Слабые места (где нужна помощь)

- Парсер subject для нестандартных документов
- Расширение словаря категорий check_subject
- Интеграция с реальным OCR (Tesseract) — пока out of scope
