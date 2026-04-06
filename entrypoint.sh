#!/bin/sh

ENV_FILE="${NTFY_ENV_FILE:-/app/.ntfy.env}"

mkdir -p "$(dirname "$ENV_FILE")"

cat >"$ENV_FILE" <<EOF
USER=${NTFY_USER}
PASSWORD=${NTFY_PASSWORD}
SERVER=${NTFY_SERVER}
DEFAULT_TOPIC=${NTFY_TOPIC:-DEFAULT}
EOF

chmod 600 "$ENV_FILE"

exec "$@"
