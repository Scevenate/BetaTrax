FROM ghcr.io/astral-sh/uv:python3.13-bookworm-slim
WORKDIR /app
COPY . .
RUN uv sync
ENV PYTHONUNBUFFERED=1
CMD ["uv", "run", "up.py"]