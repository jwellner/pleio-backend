FROM python:3.9.9-slim AS build

RUN apt-get update && apt-get install --no-install-recommends -y \
    build-essential \
    libpq-dev \
    python3-dev \
    default-libmysqlclient-dev \
    git

RUN python -m venv /app-tmp/venv && /app-tmp/venv/bin/pip install --upgrade pip

WORKDIR /app-tmp
COPY requirements.txt /app-tmp
RUN /app-tmp/venv/bin/pip3 install -r requirements.txt

FROM python:3.9.9-slim

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
    ca-certificates \
    gnupg \
    wget \
    lsb-release 

# Install postgresql client version 12
RUN mkdir -p /usr/share/man/man1/ /usr/share/man/man3/ /usr/share/man/man7/
RUN wget --quiet -O - https://www.postgresql.org/media/keys/ACCC4CF8.asc | apt-key add -
RUN echo "deb http://apt.postgresql.org/pub/repos/apt/ `lsb_release -cs`-pgdg main" | tee  /etc/apt/sources.list.d/pgdg.list
RUN apt-get update && apt-get install -y postgresql-client-12

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
