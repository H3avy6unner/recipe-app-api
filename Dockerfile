FROM python:3.9-alpine3.16
LABEL maintainer="tom.altmann@altnetz.de"

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set work directory
WORKDIR /app

# Copy requirements
COPY ./requirements.txt /tmp/requirements.txt

# Copy project files
COPY ./app /app

# Install Python dependencies
RUN apk add --no-cache build-base postgresql-dev libpq && \
    python -m venv /py && \
    /py/bin/pip install --no-cache --upgrade pip && \
    /py/bin/pip install --no-cache -r /tmp/requirements.txt && \
    rm -rf /tmp/* && \
    apk del build-base postgresql-dev && \
    adduser \
        --disabled-password \
        django-user

# Activate venv as default
ENV PATH="/py/bin:$PATH"

# Expose port (default Django port)
EXPOSE 8000

USER django-user