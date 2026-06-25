#!/bin/bash
# SSL is now automatic via Docker Compose (certbot service).
# This script only ensures env vars are set and restarts the stack.

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DOMAIN="${1:-redfox.loyalitsolution.com}"
EMAIL="${2:-admin@${DOMAIN}}"

cd "$SCRIPT_DIR"

if [ -f .env ]; then
    if ! grep -q '^SSL_DOMAIN=' .env; then
        echo "SSL_DOMAIN=${DOMAIN}" >> .env
    fi
    if ! grep -q '^CERTBOT_EMAIL=' .env; then
        echo "CERTBOT_EMAIL=${EMAIL}" >> .env
    fi
else
    cp .env.example .env
    echo "SSL_DOMAIN=${DOMAIN}" >> .env
    echo "CERTBOT_EMAIL=${EMAIL}" >> .env
    echo "Created .env from .env.example — set POSTGRES_PASSWORD before continuing."
fi

mkdir -p certbot-webroot letsencrypt

echo "Starting stack with automatic SSL for ${DOMAIN}..."
docker compose up -d

echo ""
echo "SSL will be obtained automatically once DNS points to this server."
echo "Watch progress: docker compose logs -f certbot"
echo "Site URL: https://${DOMAIN}"