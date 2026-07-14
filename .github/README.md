# GitHub Actions workflow — пример

Файл `ci.yml.example` — это готовый workflow для GitHub Actions, который
запускает `pytest` на Python 3.11 и 3.12 при каждом push или Pull Request.

## Почему это пример, а не активный workflow

GitHub требует, чтобы у Personal Access Token был scope `workflow` для
создания или изменения файлов в `.github/workflows/`. Токен, использованный
для первоначального пуша репозитория, не имеет этого scope (это нормально —
так безопаснее).

## Как активировать

1. Скопируй файл в правильное место:
   ```bash
   mv .github/ci.yml.example .github/workflows/ci.yml
   ```
2. Закоммить и запуш:
   ```bash
   git add .github/workflows/ci.yml
   git commit -m "ci: activate GitHub Actions workflow"
   git push
   ```
3. Готово — на вкладке **Actions** в репозитории появятся запуски.

## Что делает workflow

- Триггер: `push` в любую ветку, `pull_request` в `main`.
- Матрица: Python 3.11 + 3.12.
- Шаги: checkout → setup Python (с кэшем pip) → `pip install -e ".[dev,api]"` → `pytest -v` → `python -m credit_check.metrics`.
- `concurrency` отменяет предыдущие запуски на тот же коммит — экономит минуты.

После активации бейдж CI в README начнёт отображать реальный статус.
