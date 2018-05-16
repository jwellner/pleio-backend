FROM python:3

# Install app dependencies
RUN mkdir /app
WORKDIR /app
ADD requirements.txt /app
RUN pip install --no-cache-dir -r requirements.txt

# Add app
ADD . /app

# Boot script
ADD docker/config.py /app/backend2/config.py
ADD docker/start.sh /start.sh
RUN chmod +x /start.sh

# HTTP port
EXPOSE 8000

# Define run script
CMD ["/start.sh"]
