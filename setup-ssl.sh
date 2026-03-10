#!/bin/bash
# SSL certificate setup for Odoo with Let's Encrypt
# Run this on your Ubuntu server

set -e

DOMAIN="${1:-redfox.loyalitsolution.com}"
export CERTBOT_EMAIL="${2:-}"

if [ -z "$1" ]; then
    echo "Using default domain: ${DOMAIN}"
    echo "(Override with: ./setup-ssl.sh your-domain.com [email])"
fi
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CERTBOT_WEBROOT="${SCRIPT_DIR}/certbot-webroot"

echo "=== SSL Setup for ${DOMAIN} ==="

# 1. Ensure domain points to this server
echo ""
echo "Ensure ${DOMAIN} DNS points to this server's IP before continuing."
read -p "Press Enter to continue..."

# 2. Install Certbot if needed
if ! command -v certbot &> /dev/null; then
    echo "Installing Certbot..."
    sudo apt update
    sudo apt install -y certbot
fi

# 3. Create webroot directory
mkdir -p "$CERTBOT_WEBROOT"

# 4. Use HTTP-only config for initial cert (Nginx can't start with SSL until certs exist)
echo "Switching to HTTP-only config for certificate acquisition..."
cp "${SCRIPT_DIR}/nginx/odoo-http-only.conf" "${SCRIPT_DIR}/nginx/odoo.conf"

# 5. Ensure Nginx is running (needed for webroot challenge)
echo "Restarting Nginx..."
cd "$SCRIPT_DIR"
(docker compose up -d nginx 2>/dev/null || docker-compose up -d nginx 2>/dev/null) || true
sleep 2

# 6. Obtain certificate
echo "Obtaining certificate from Let's Encrypt..."
sudo certbot certonly --webroot \
    -w "$CERTBOT_WEBROOT" \
    -d "$DOMAIN" \
    --email "${CERTBOT_EMAIL:-admin@${DOMAIN}}" \
    --agree-tos \
    --non-interactive

# 7. Switch to SSL config for HTTPS
echo "Updating Nginx config for HTTPS..."
cp "${SCRIPT_DIR}/nginx/odoo-ssl.conf" "${SCRIPT_DIR}/nginx/odoo.conf"

# 8. Restart Nginx with SSL
echo "Restarting Nginx with SSL..."
docker compose restart nginx 2>/dev/null || docker-compose restart nginx 2>/dev/null

echo ""
echo "=== SSL setup complete! ==="
echo "Your Odoo site is now available at: https://${DOMAIN}"
echo ""
echo "To auto-renew certs, add to crontab (crontab -e):"
echo "  0 3 1 * * ${SCRIPT_DIR}/renew-ssl.sh"
