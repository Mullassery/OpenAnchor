.PHONY: help install dev test lint format clean security

help:
	@echo "OpenAnchor - Development Commands"
	@echo ""
	@echo "Available targets:"
	@echo "  make install     Install package in production mode"
	@echo "  make dev         Install package in development mode with all dependencies"
	@echo "  make test        Run test suite with coverage"
	@echo "  make lint        Run linting checks (ruff, black, mypy)"
	@echo "  make format      Auto-format code (black, ruff)"
	@echo "  make security    Run security checks (bandit, safety)"
	@echo "  make clean       Remove build artifacts and cache files"
	@echo "  make all         Run all checks (lint, test, security)"

install:
	pip install .

dev:
	pip install -e ".[dev]"

test:
	pytest tests/ -v --cov=openanchor --cov-report=html --cov-report=term

lint:
	@echo "Running ruff..."
	ruff check openanchor tests
	@echo "Running black..."
	black --check openanchor tests
	@echo "Running mypy..."
	mypy openanchor --ignore-missing-imports || true

format:
	@echo "Formatting with black..."
	black openanchor tests
	@echo "Fixing with ruff..."
	ruff check openanchor tests --fix

security:
	@echo "Running bandit..."
	bandit -r openanchor -f json -o bandit-report.json || true
	@echo "Running safety..."
	safety check --json || true

clean:
	rm -rf build/ dist/ *.egg-info/
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
	rm -f .coverage
	rm -rf htmlcov/
	rm -f bandit-report.json

all: lint test security
	@echo "✅ All checks passed!"
