VENV      := .venv
PYTHON    := $(VENV)/bin/python
PIP       := $(VENV)/bin/pip
RUFF      := $(VENV)/bin/ruff
PYTEST    := $(VENV)/bin/pytest
PRECOMMIT := $(VENV)/bin/pre-commit
STREAMLIT := $(VENV)/bin/streamlit

.DEFAULT_GOAL := help

.PHONY: help venv install install-dev lint format test run clean

help:            ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?##' $(MAKEFILE_LIST) | awk 'BEGIN{FS=":.*?## "}{printf "  \033[36m%-14s\033[0m %s\n",$$1,$$2}'

venv:            ## Create the virtual environment
	python3 -m venv $(VENV)
	$(PIP) install --upgrade pip --quiet

install: venv    ## Install runtime dependencies into .venv
	$(PIP) install -r requirements.txt --quiet
	@echo "Runtime dependencies installed."

install-dev: venv  ## Install all dev dependencies and activate pre-commit hooks
	$(PIP) install -r requirements-dev.txt --quiet
	$(PRECOMMIT) install
	@echo "Dev dependencies installed and pre-commit hooks registered."

lint:            ## Run ruff linter
	$(RUFF) check .

format:          ## Auto-format with ruff
	$(RUFF) format .

test:            ## Run the test suite
	$(PYTEST) tests/ -v --tb=short

run:             ## Launch the Streamlit web app
	$(STREAMLIT) run app.py

clean:           ## Remove .venv and all caches
	rm -rf $(VENV) __pycache__ .pytest_cache .ruff_cache
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
