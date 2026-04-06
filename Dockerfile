FROM python:3.14-alpine

RUN apk add --no-cache \
    tzdata \
    git \
    bash

WORKDIR /app

RUN adduser \
    --disabled-password \
    --gecos "" \
    --home "/nonexistent" \
    --shell "/sbin/nologin" \
    --no-create-home \
    --uid "10001" \
    app

# ntfy-send installieren (robust)
RUN git clone https://github.com/maralexofficial/ntfy-send.git /tmp/ntfy-send && \
    ls -la /tmp/ntfy-send && \
    find /tmp/ntfy-send -type f -name "*ntfy-send*" && \
    cp $(find /tmp/ntfy-send -type f -name "*ntfy-send*" | head -n 1) /usr/bin/ntfy-send && \
    chmod +x /usr/bin/ntfy-send && \
    mkdir -p /etc/ntfy-send && \
    if [ -f /tmp/ntfy-send/.env.example ]; then cp /tmp/ntfy-send/.env.example /etc/ntfy-send/.env; fi && \
    chmod 644 /etc/ntfy-send/.env 2>/dev/null || true && \
    rm -rf /tmp/ntfy-send

# Python deps
RUN --mount=type=cache,target=/root/.cache/pip \
    --mount=type=bind,source=requirements.txt,target=requirements.txt \
    python -m pip install -r requirements.txt

USER app

COPY snapshot-as-backup.py README.md LICENSE ./
COPY lib ./lib

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV IN_DOCKER_CONTAINER=true

CMD [ "python3", "-u", "/app/snapshot-as-backup.py"]