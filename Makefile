.PHONY: install test lint metrics plots api docker clean

install:
	pip install -e ".[dev,api]"

test:
	pytest -v

test-fast:
	pytest -x --tb=short

metrics:
	python -m credit_check.metrics

plots:
	python scripts/generate_plots.py

api:
	uvicorn credit_check.api:app --reload --port 8000

docker:
	docker build -t credit-check:0.6.0 .
	docker run --rm -p 8000:8000 credit-check:0.6.0

clean:
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type d -name .pytest_cache -exec rm -rf {} +
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	rm -rf build dist .coverage htmlcov
