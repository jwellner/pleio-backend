FROM python:3.6-slim

# Workaround for error with postgresql-client package
RUN mkdir -p /usr/share/man/man1/ /usr/share/man/man3/ /usr/share/man/man7/

RUN apt-get update && apt-get install --no-install-recommends -y \
    git \
    build-essential

WORKDIR /app
COPY requirements.txt /app
RUN pip3 install -r requirements.txt

# App assets
COPY . /app
COPY ./docker/start.sh ./docker/start-dev.sh /
COPY ./docker/config.py ./backend2/
RUN chmod +x /start.sh /start-dev.sh

# Create media and static folders
RUN mkdir -p /app/media /app/static && chown www-data:www-data /app/media /app/static

ENV PYTHONUNBUFFERED 1
EXPOSE 8000
USER www-data
