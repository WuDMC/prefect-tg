install:
	pip install --upgrade pip &&\
	pip install -r requirements.txt &&\
    pip install -e libs/tg_jobs_parser_module

test:
	python -m pytest -v -s --show-capture=all tests/test_cloud.py

format:
	black tests
	find . -path ./venv -prune -o -name "*.py" -exec black {} +

lint:
	pylint --disable=R,C *.py

all: install test format