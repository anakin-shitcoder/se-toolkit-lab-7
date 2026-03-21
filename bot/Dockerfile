# Telegram Bot Dockerfile
# Uses uv for dependency management

FROM python:3.12-slim

WORKDIR /app

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Copy lockfile first for better caching
COPY uv.lock ./

# Copy project files (Dockerfile is in bot/ directory)
COPY pyproject.toml ./
COPY bot.py config.py ./
COPY handlers/ ./handlers/
COPY services/ ./services/

# Install dependencies (use --frozen since we have uv.lock)
RUN uv sync --frozen --no-dev

# Set Python path
ENV PYTHONPATH=/app

# Run the bot
CMD ["uv", "run", "bot.py"]
