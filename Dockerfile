FROM python:3.12-slim
# Prevent Python from writing .pyc files and enable unbuffered logging
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
WORKDIR /app
# Install system dependencies needed for compiling C extensions like psycopg2
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*
# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
# Copy application source code
COPY . .
# Expose port 8000
EXPOSE 8000
# Start Uvicorn web server
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]