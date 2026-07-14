# Changelog

Все заметные изменения проекта документируются здесь.
Формат основан на [Keep a Changelog](https://keepachangelog.com/),
проект следует [Semantic Versioning](https://semver.org/).

## [0.6.0] — 2026-07-15

### Добавлено
- 4 новые категории check_subject: животноводство, овощи и фрукты, рыбоводство, лесное хозяйство
- 11 новых парсеров: КПП, ОГРН, БИК, р/с, к/с, email, телефон, № документа, НДС, адрес, валюта
- Метрики precision/recall/F1/confusion matrix + средняя confidence
- 2 новых графика: confusion matrix + распределение confidence check_subject
- Поддержка ISO даты YYYY-MM-DD
- Поддержка сокращений суммы: тыс./млн./млрд. руб.
- Расширены все категории (корма, семена, техника, топливо, запчасти, агрохимия)
- Запрещённые слова: маркетинг, SMM, таргет, ресторан, кафе, общепит
- Сильные сельхоз-контексты: КФХ, агроконсалт, агроаудит
- Парсер contractor: поддержка СПК, КФХ, НКО
- API endpoint /version
- CLI --version
- 275+ тестов (edge cases, stress, на реальных файлах)
- CHANGELOG.md, CONTRIBUTING.md, SECURITY.md, .editorconfig, Makefile, .python-version
- Конфиги ruff/mypy/coverage в pyproject.toml
- tests/conftest.py с общими fixtures

### Изменено
- Расширены категории: корма (+БВМД, стартер), семена (+элита, репродукция),
  техника (+New Holland, Claas, Case), топливо (+керосин, мазут, СУГ),
  запчасти (+фильтр, ремень, подшипник), агрохимия (+аммофос, суперфосфат)

## [0.5.0] — 2026-07-14

### Добавлено
- 3 графика matplotlib для README
- Таблица extract с колонкой «что пропущено»
- Числовой эксперимент с порогом classify (8 порогов)
- MOTIVATION.md — мотивация вынесена из README

## [0.4.0] — 2026-07-14

### Добавлено
- Фикс EDGE-кейса «агроном-консультант»: белый список _STRONG_AGRI_CONTEXT
- GitHub Actions CI (как пример, требует ручной активации)
- Dockerfile, .dockerignore, .env.example, LICENSE

## [0.3.0] — 2026-07-14

### Добавлено
- Метрики качества (credit_check.metrics)
- FastAPI-обёртка (credit_check.api)
- Парсер суммы прописью: миллиарды, триллионы, дробные
- Парсер дат: приоритет срока оплаты для invoice

## [0.2.0] — 2026-07-14

### Добавлено
- Реализация extract/classify/check_subject
- 98 тестов, README с 6 разделами, RESULTS.md
