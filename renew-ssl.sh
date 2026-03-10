#!/bin/bash
# Cert renewal - run via cron (e.g. monthly)
# Crontab: 0 3 1 * * /path/to/redfox/renew-ssl.sh

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CERTBOT_WEBROOT="${SCRIPT_DIR}/certbot-webroot"

certbot renew --webroot -w "$CERTBOT_WEBROOT" --quiet
cd "$SCRIPT_DIR"
docker compose restart nginx 2>/dev/null || docker-compose restart nginx 2>/dev/null || true
