FROM python:3.14-alpine

RUN apk add --no-cache tzdata git bash

WORKDIR /app

# Installation als root
RUN git clone https://github.com/maralexofficial/ntfy-send.git /tmp/ntfy-send && \
    install -m 755 /tmp/ntfy-send/ntfy-send.sh /usr/bin/ntfy-send && \
    mkdir -p /etc/ntfy-send && \
    install -m 644 /tmp/ntfy-send/.env.example /etc/ntfy-send/.env && \
    rm -rf /tmp/ntfy-send

COPY requirements.txt .
RUN pip install -r requirements.txt

RUN adduser \
    --disabled-password \
    --gecos "" \
    --home "/nonexistent" \
    --shell "/sbin/nologin" \
    --no-create-home \
    --uid "10001" \
    app

USER app

COPY snapshot-as-backup.py README.md LICENSE ./
COPY lib ./lib

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV IN_DOCKER_CONTAINER=true

CMD ["python3", "-u", "/app/snapshot-as-backup.py"]