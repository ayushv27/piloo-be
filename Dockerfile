# Use Python 3.11 on Debian Bullseye (wkhtmltopdf available in apt)
FROM python:3.11-bullseye

# Environment settings
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Set working directory
WORKDIR /code

# Install system dependencies in one layer
RUN apt-get update && apt-get upgrade -y && \
    apt-get install -y \
    build-essential \
    libffi-dev \
    libcairo2 \
    libpango-1.0-0 \
    libpangocairo-1.0-0 \
    libgdk-pixbuf2.0-0 \
    libjpeg-dev \
    libxml2 \
    libxslt1.1 \
    libssl-dev \
    shared-mime-info \
    curl \
    wkhtmltopdf \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt /code/
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . /code/
