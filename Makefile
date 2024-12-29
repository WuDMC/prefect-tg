# Makefile for Prefect project
include .env

.PHONY: install login init run test format lint all submodule

install:
	git submodule update --init --recursive && \
	pip install --upgrade pip && \
	pip install -r requirements.txt && \
	pip install -e libs/tg_jobs_parser_module && \
	pip install -U prefect && \

login:
	prefect cloud login --key "$(PREFECT_API_KEY)" --workspace "$(WORKSPACE)"


deploy:
	prefect deploy --prefect-file prefect.yaml --all

run:
	prefect worker start --pool VM

test:
	python -m pytest -v -s --show-capture=all tests/

format:
	black tests
	black *.py

lint:
	pylint --disable=R,C *.py

submodule:
	git submodule update --remote libs/tg_jobs_parser_module

all: install login deploy run