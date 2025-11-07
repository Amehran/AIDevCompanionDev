# Base image (stick to 3.11 due to NumPy 1.26 pin and broad compatibility)
FROM python:3.11-slim

# Environment settings for predictable Python behavior
ENV PYTHONDONTWRITEBYTECODE=1 \
        PYTHONUNBUFFERED=1 \
        PIP_NO_CACHE_DIR=1

# Set working directory
WORKDIR /app

# Install system dependencies (curl for healthcheck, gcc for any wheels that need compile)
RUN apt-get update && apt-get install -y --no-install-recommends \
        gcc \
        curl \
    && rm -rf /var/lib/apt/lists/*

# Install Poetry 2.x to match lock format (supports PEP 621 [project])
RUN pip install "poetry==2.2.1"

# Copy Poetry configuration files first for better caching
COPY pyproject.toml poetry.lock* ./

# Configure Poetry to install into the system (no venv)
RUN poetry config virtualenvs.create false

# Install project dependencies (without installing the project itself)
RUN poetry install --no-interaction --no-ansi --no-root

# Copy the rest of the application
COPY . .

# Create a non-root user and adjust ownership
RUN useradd --create-home --shell /bin/bash appuser \
    && chown -R appuser:appuser /app
USER appuser

# Expose the port the app runs on
EXPOSE 8000

# Optional container healthcheck (expects 200 on GET /)
HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
    CMD curl -fsS http://localhost:8000/ || exit 1

# Run the application (uvicorn installed globally because Poetry used --no-venv)
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
