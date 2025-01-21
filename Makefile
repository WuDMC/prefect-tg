# Makefile for Prefect project
include .env

VENV_DIR = venv
PYTHON = python3

.PHONY: install login deploy run test format lint submodule venv clean all

# Target to create and set up a virtual environment
venv:
	@echo "Creating virtual environment in $(VENV_DIR)..."
	@if [ ! -d "$(VENV_DIR)" ]; then \
		$(PYTHON) -m venv $(VENV_DIR); \
		$(VENV_DIR)/bin/python -m pip install --upgrade pip; \
	else \
		echo "Virtual environment already exists."; \
	fi

install: venv
	@echo "Installing dependencies..."
	git submodule update --init --recursive && \
	$(VENV_DIR)/bin/pip install -r requirements.txt && \
	$(VENV_DIR)/bin/pip install -e libs/tg_jobs_parser_module && \
	$(VENV_DIR)/bin/pip install -U prefect

login:
	@echo "Logging into Prefect Cloud..."
	$(VENV_DIR)/bin/prefect cloud login --key "$(PREFECT_API_KEY)" --workspace "$(WORKSPACE)"

deploy:
	@echo "Deploying flows..."
	$(VENV_DIR)/bin/prefect deploy --prefect-file prefect.yaml --all

run:
	@echo "Starting Prefect worker..."
	$(VENV_DIR)/bin/prefect worker start --pool local

test:
	@echo "Running tests..."
	$(VENV_DIR)/bin/python -m pytest -v -s --show-capture=all tests/

format:
	@echo "Formatting code with Black..."
	$(VENV_DIR)/bin/black tests
	$(VENV_DIR)/bin/black *.py

lint:
	@echo "Linting with Pylint..."
	$(VENV_DIR)/bin/pylint --disable=R,C *.py

submodule:
	@echo "Updating submodule..."
	git submodule update --remote libs/tg_jobs_parser_module

clean:
	@echo "Cleaning up virtual environment..."
	rm -rf $(VENV_DIR)

all: install login deploy run
