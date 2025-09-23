.PHONY: help install install-dev test test-unit test-integration test-cov lint format clean

help: ## Show this help message
	@echo "Available commands:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

install: ## Install the package
	pip install .

install-dev: ## Install the package with development dependencies
	pip install -e ".[dev]"

test: ## Run all tests
	pytest

test-unit: ## Run unit tests only
	pytest -m "not integration"

test-integration: ## Run integration tests only (requires API keys)
	pytest -m integration

test-cov: ## Run tests with coverage report
	pytest --cov=src/pydc_mem --cov-report=html --cov-report=term

lint: ## Run linting checks
	flake8 src/ tests/
	mypy src/
	isort --check-only src/ tests/
	black --check src/ tests/

format: ## Format code
	black src/ tests/
	isort src/ tests/

clean: ## Clean up build artifacts
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info/
	rm -rf src/*.egg-info/
	rm -rf .pytest_cache/
	rm -rf .coverage
	rm -rf htmlcov/
	find . -type d -name __pycache__ -delete
	find . -type f -name "*.pyc" -delete

ci: ## Run CI checks (lint + test)
	make lint
	make test-unit
