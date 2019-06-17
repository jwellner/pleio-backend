FROM python:3

# Install app dependencies
COPY . /app
WORKDIR /app

RUN pip install --no-cache-dir -r requirements.txt

# Boot script
COPY docker/start.sh /start.sh
COPY docker/start-dev.sh /start-dev.sh
RUN chmod +x /start.sh
RUN chmod +x /start-dev.sh

# HTTP port
EXPOSE 8000
