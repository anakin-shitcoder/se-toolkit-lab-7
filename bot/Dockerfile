# Telegram Bot Dockerfile
# Uses uv for dependency management

FROM python:3.14-slim

WORKDIR /app

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Copy lockfile from parent directory (Dockerfile is in bot/)
COPY ../pyproject.toml ./

# Copy project files
COPY bot/bot.py bot/config.py ./
COPY bot/handlers/ ./handlers/
COPY bot/services/ ./services/

# Install dependencies (regenerate lock if needed)
RUN uv sync --no-dev

# Set Python path
ENV PYTHONPATH=/app

# Run the bot
CMD ["uv", "run", "bot.py"]
