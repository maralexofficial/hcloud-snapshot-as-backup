FROM python:3.14-alpine

RUN apk add --no-cache tzdata git bash

WORKDIR /app

# Installation als root
RUN git clone https://github.com/maralexofficial/ntfy-send.git /tmp/ntfy-send && \
    install -m 755 /tmp/ntfy-send/ntfy-send.sh /usr/bin/ntfy-send && \
    mkdir -p /etc/ntfy-send && \
    install -m 644 /tmp/ntfy-send/.env.example /etc/ntfy-send/.env && \
    rm -rf /tmp/ntfy-send

RUN pip install -r requirements.txt

# User erst NACH Installation
RUN adduser \
    --disabled-password \
    --gecos "" \
    --uid "10001" \
    app

USER app

COPY snapshot-as-backup.py README.md LICENSE ./
COPY lib ./lib

ENV PATH="/usr/bin:${PATH}"

CMD ["python3", "-u", "/app/snapshot-as-backup.py"]