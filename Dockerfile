FROM python:3.13-slim
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV UV_NO_DEV=1
ENV BROWSER_PATH=/usr/bin/chromium

RUN apt-get update && apt-get install -y chromium

COPY . /app
WORKDIR /app

RUN uv sync --locked

CMD ["uv", "run", "src/trackabee/main.py"]
