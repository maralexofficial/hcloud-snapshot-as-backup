FROM python:3.14-alpine

RUN apk add --no-cache \
    tzdata \
    git \
    bash \
    curl \
    su-exec \
    tzdata

WORKDIR /app

RUN adduser \
    --disabled-password \
    --gecos "" \
    --home "/nonexistent" \
    --shell "/sbin/nologin" \
    --no-create-home \
    --uid "10001" \
    app

RUN mkdir -p /app && chown -R 10001:10001 /app

RUN git clone https://github.com/maralexofficial/ntfy-send.git /tmp/ntfy-send && \
    cp /tmp/ntfy-send/ntfy-send.sh /usr/bin/ntfy-send && \
    chmod 755 /usr/bin/ntfy-send && \
    rm -rf /tmp/ntfy-send

COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

RUN --mount=type=cache,target=/root/.cache/pip \
    --mount=type=bind,source=requirements.txt,target=requirements.txt \
    python -m pip install -r requirements.txt

COPY snapshot-as-backup.py README.md LICENSE ./
COPY lib ./lib

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV IN_DOCKER_CONTAINER=true

USER app

ENTRYPOINT ["/entrypoint.sh"]
CMD [ "python3", "-u", "/app/snapshot-as-backup.py"]