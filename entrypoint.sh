#!/bin/sh

ENV_FILE="/etc/ntfy-send/.env"

mkdir -p /etc/ntfy-send

cat >"$ENV_FILE" <<EOF
USER=${NTFY_USER}
PASSWORD=${NTFY_PASSWORD}
SERVER=${NTFY_SERVER}
DEFAULT_TOPIC=${NTFY_TOPIC:-DEFAULT}
EOF

chmod 600 "$ENV_FILE"

exec "$@"
