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
RUN apk add --no-cache bash postgresql-client jpeg-dev libpq && \
    apk add --no-cache --virtual .tmp-build-deps \
        build-base postgresql-dev musl-dev zlib zlib-dev && \
    python -m venv /py && \
    /py/bin/pip install --no-cache --upgrade pip && \
    /py/bin/pip install --no-cache -r /tmp/requirements.txt && \
    rm -rf /tmp/* && \
    apk del .tmp-build-deps && \
    adduser \
        --disabled-password \
        django-user && \
    mkdir -p /vol/web/media && \
    mkdir -p /vol/web/static && \
    chown -R django-user:django-user /vol && \
    chmod -R 755 /vol 

# Activate venv as default
ENV PATH="/py/bin:$PATH"

# Expose port (default Django port)
EXPOSE 8000

USER django-user