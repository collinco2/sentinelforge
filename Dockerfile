# Use an official Python runtime as a parent image
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
ENV PIP_NO_CACHE_DIR=off
ENV PIP_DISABLE_PIP_VERSION_CHECK=on
# Add WORKDIR to PYTHONPATH
ENV PYTHONPATH="${PYTHONPATH}:/app"

# Create and set the working directory
WORKDIR /app

# Install system dependencies if any (e.g., for libraries needing compilation)
# RUN apt-get update && apt-get install -y --no-install-recommends gcc && rm -rf /var/lib/apt/lists/*

# Copy only pyproject.toml first to leverage Docker cache for dependencies
COPY pyproject.toml pyproject.toml

# Install project dependencies (excluding dev dependencies)
# Let pip handle resolving dependencies listed in [project].dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir .

# Copy the rest of the application code
COPY ./sentinelforge ./sentinelforge

# Copy necessary configuration and template files
COPY scoring_rules.yaml .
COPY sentinelforge/config/nlp_summarizer.json ./sentinelforge/config/
COPY sentinelforge/notifications/templates ./sentinelforge/notifications/templates

# Create directory for database and models (won't be persisted unless mounted)
RUN mkdir -p /app/data
RUN mkdir -p /app/models

# Expose the port the API server runs on
EXPOSE 8000 
# Note: The __main__.py runs on 8080, but the entrypoint runs taxii:app which defaults to 8000 unless configured
# Consider unifying the ports or making the API port configurable via settings.py

# Define the command to run the application using uvicorn directly
# This ensures the module path is correctly handled by Python
CMD ["uvicorn", "sentinelforge.api.taxii:app", "--host", "0.0.0.0", "--port", "8000"] 