FROM python:3.11
ENV PYTHONDONTWRITEBYTECODE=1
# ENV PIP_DISABLE_PIP_VERSION_CHECK on
ENV PYTHONUNBUFFERED=1
WORKDIR /code
COPY requirements.txt /code/
RUN apt-get -y update && apt-get -y upgrade
RUN apt update && apt install curl
RUN pip install --no-cache-dir -r requirements.txt 
# Install system dependencies for WeasyPrint
RUN apt-get update && apt-get install -y \
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
# RUN apt install libpango1.0-0 libpangocairo-1.0-0 libffi-dev libcairo2

COPY . /code/