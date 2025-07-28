FROM python:3.11-slim

WORKDIR /app

# Install system dependencies including Docker
RUN apt-get update && apt-get install -y \
    curl \
    docker.io \
    && rm -rf /var/lib/apt/lists/*

# Install Poetry
RUN pip install poetry

# Copy poetry files
COPY pyproject.toml poetry.lock* ./

# Configure poetry
RUN poetry config virtualenvs.create false

# Install dependencies
RUN poetry install --no-dev

# Copy application code
COPY . .

# Create logs directory
RUN mkdir -p /app/logs

# Run the application
CMD ["poetry", "run", "python", "-m", "app.main"]
