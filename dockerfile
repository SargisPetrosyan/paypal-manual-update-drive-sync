FROM python:3.13-slim

COPY --from=ghcr.io/astral-sh/uv:0.9.11 /uv /uvx /bin/

WORKDIR /app

COPY . .

RUN uv sync --locked

CMD ["python3", "run", "-m", "app.main"]