#!/bin/bash
# Manual certificate renewal trigger (renewal also runs automatically in certbot container)

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

docker compose exec certbot certbot renew --webroot -w /var/www/certbot
docker compose restart nginx
