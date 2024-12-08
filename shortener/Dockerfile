# Starting from a lightweight Python base image.
FROM python:3.11-slim

# Set environment variables to avoid bytecode and ensure unbuffered output.
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Ensure Python can find modules under /app/src.
ENV PYTHONPATH=/app/src

# Set the working directory inside the container.
WORKDIR /app

# Install system dependencies if needed (for Postgres, Redis clients, etc.).
# For example, if you need build tools or specific libs:
# RUN apt-get update && apt-get install -y libpq-dev && rm -rf /var/lib/apt/lists/*

# Copy and install Python dependencies.
COPY requirements.txt .
RUN pip install --upgrade pip && pip install --no-cache-dir -r requirements.txt

# Copy application source code into /app/src.
# Ensure each directory inside src has __init__.py so they are recognized as packages.
COPY . .

# If you have a schema.sql or other files, copy them if needed:
# COPY schema.sql /app/schema.sql

# Expose the API port.
EXPOSE 8080

# Run the application using Uvicorn.
# Adjust "shortener.app:app" to match your actual Python module and FastAPI app instance.
# If your main FastAPI app object is in app.py under src, you might do:
# CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8080"]
#
# If you've organized your code so that the entry point is `shortener.app:app` inside src/shortener,
# then you would run it as:
CMD ["uvicorn", "shortener.app:app", "--host", "0.0.0.0", "--port", "8080"]
