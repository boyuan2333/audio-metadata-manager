.PHONY: help install dev test lint clean index search similar review

help:
	@echo "Audio Metadata Manager - Development Commands"
	@echo ""
	@echo "  install     - Install dependencies from requirements.txt"
	@echo "  dev         - Install with dev dependencies (pytest, coverage)"
	@echo "  test        - Run all tests with coverage"
	@echo "  test-verbose- Run tests with verbose output"
	@echo "  lint        - Run basic linting (future: ruff/black)"
	@echo "  clean       - Remove __pycache__ and .pyc files"
	@echo ""
	@echo "CLI Commands:"
	@echo "  index       - Run index command (requires --input --output)"
	@echo "  search      - Run search command (requires --input)"
	@echo "  similar     - Run similar command (requires --input --reference)"
	@echo "  review      - Run review command (requires --input --id)"
	@echo ""
	@echo "Git:"
	@echo "  status      - Show git status"
	@echo "  diff        - Show git diff"
	@echo "  commit      - Create commit (requires MSG=)"

install:
	pip install -r requirements.txt

dev:
	pip install -r requirements.txt
	pip install pytest pytest-cov

test:
	python -m pytest tests/ -v --cov=. --cov-report=term-missing

test-verbose:
	python -m pytest tests/ -vv -s --tb=long

lint:
	@echo "Linting (placeholder - add ruff/black config as needed)"

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete

index:
	python app.py index $(filter-out $@,$(MAKECMDGOALS))

search:
	python app.py search $(filter-out $@,$(MAKECMDGOALS))

similar:
	python app.py similar $(filter-out $@,$(MAKECMDGOALS))

review:
	python app.py review $(filter-out $@,$(MAKECMDGOALS))

status:
	git status

diff:
	git diff

commit:
ifndef MSG
	$(error MSG is required. Usage: make commit MSG="commit message")
endif
	git commit -m "$(MSG)"
