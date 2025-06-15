# Dockerfile for the transcritor-pdf service

# Use a slim Python image for a smaller final build.
FROM python:3.11-slim

# Set the working directory in the container.
WORKDIR /app

# Install OS-level dependencies required for Python packages (e.g., psycopg2, scikit-image).
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
 && apt-get clean \
 && rm -rf /var/lib/apt/lists/*

# Copy and install Python requirements, leveraging Docker's build cache.
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy the application source code into the container.
COPY . .

# Expose the port the API will listen on.
EXPOSE 8002

# Default command to run the application.
# This is typically overridden by the 'command' in docker-compose.yml for development.
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8002"]
