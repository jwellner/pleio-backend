FROM python:3-jessie

COPY . .
RUN pip3 install -r requirements.txt
RUN cp backend/config.example.py ./config.py

ENTRYPOINT ["/bin/bash"]
