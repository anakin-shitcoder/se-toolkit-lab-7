# Telegram Bot Dockerfile
# Uses uv for dependency management

FROM python:3.12-slim

WORKDIR /app

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Copy project files
COPY pyproject.toml uv.lock* ./
COPY bot/ ./bot/
COPY services/ ./services/
COPY handlers/ ./handlers/
COPY config.py ./

# Install dependencies
RUN uv sync --frozen --no-dev

# Set Python path
ENV PYTHONPATH=/app

# Run the bot
CMD ["uv", "run", "bot/bot.py"]
