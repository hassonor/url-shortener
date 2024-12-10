# Use multi-stage to reduce image size
FROM python:3.11-slim as builder

WORKDIR /app
COPY requirements.txt .

# Install build deps for building Python packages
RUN apt-get update && apt-get install -y build-essential && rm -rf /var/lib/apt/lists/*

RUN pip install --upgrade pip && pip wheel --no-cache-dir --wheel-dir /app/wheels -r requirements.txt

FROM python:3.11-slim

WORKDIR /app

# Install runtime dependencies (no build-essential needed)
COPY --from=builder /app/wheels /wheels
RUN pip install --no-cache-dir /wheels/* && rm -rf /wheels

# Copy source
COPY . .

EXPOSE 8000 8001
CMD ["python", "src/main.py"]
