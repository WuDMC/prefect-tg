FROM prefecthq/prefect:3.1.11-python3.10

# Установить зависимости
COPY requirements.txt /opt/prefect/prefect-tg/requirements.txt
RUN python -m pip install -r /opt/prefect/prefect-tg/requirements.txt

# Скопировать весь проект
COPY . /opt/prefect/prefect-tg/

# Переключиться в директорию проекта
WORKDIR /opt/prefect/prefect-tg/

# Установить PYTHONPATH
ENV PYTHONPATH="/opt/prefect/prefect-tg/libs/tg_jobs_parser_module:$PYTHONPATH"

# Тест 1: Проверить доступность модуля через PYTHONPATH
RUN python -c "import sys; print('PYTHONPATH:', sys.path)" && \
    python -c "import tg_jobs_parser_module" || echo 'PYTHONPATH failed'

# Тест 2: Установить как editable и проверить
RUN python -m pip install libs/tg_jobs_parser_module || echo 'Editable install failed'