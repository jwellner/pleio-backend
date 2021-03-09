FROM python:3.8-slim AS build

RUN apt-get update && apt-get install --no-install-recommends -y \
    build-essential \
    libpq-dev \
    python3-dev \
    default-libmysqlclient-dev

RUN python -m venv /app-tmp/venv && /app-tmp/venv/bin/pip install --upgrade pip

WORKDIR /app-tmp
COPY requirements.txt /app-tmp
RUN /app-tmp/venv/bin/pip3 install -r requirements.txt

FROM python:3.8-slim

# Workaround for error with postgresql-client package
RUN mkdir -p /usr/share/man/man1/ /usr/share/man/man3/ /usr/share/man/man7/

RUN apt-get update && apt-get install --no-install-recommends -y \
    libgnutls30 \
    gettext \
    git \
    mime-support \
    libmagic-dev \
    libpq-dev \
    libmariadb3 \
    antiword \
    poppler-utils \
    tesseract-ocr \
    swig \
    ca-certificates

COPY --from=build /app-tmp/venv /app-tmp/venv
ENV PATH="/app-tmp/venv/bin:${PATH}"

WORKDIR /app
# App assets
COPY . /app
COPY ./docker/*.sh /
COPY ./docker/*.ini /
RUN chmod +x /*.sh

# Create media and static folders
RUN mkdir -p /app/static /app/static-frontend && chown www-data:www-data /app/static /app/static-frontend

ENV PYTHONUNBUFFERED 1
EXPOSE 8000
USER www-data
