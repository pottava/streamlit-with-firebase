FROM python:3.9-slim as poetry
ENV PYTHONUNBUFFERED=1
WORKDIR /app

ENV POETRY_HOME=/opt/poetry
ENV POETRY_VIRTUALENVS_IN_PROJECT=true
ENV PATH="${POETRY_HOME}/bin:${PATH}"
RUN python -c 'from urllib.request import urlopen; print(urlopen("https://install.python-poetry.org").read().decode())' | python -
COPY pyproject.toml /app/
COPY poetry.lock /app/
RUN poetry install --no-interaction --without dev --no-ansi -vvv

COPY . /app/
CMD ["poetry", "run", "streamlit", "run", "app.py", "--server.port", "8080"]
