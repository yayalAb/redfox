#!/bin/sh
set -e

DOMAIN="${SSL_DOMAIN:-redfox.loyalitsolution.com}"
EMAIL="${CERTBOT_EMAIL:-admin@${DOMAIN}}"
WEBROOT=/var/www/certbot
CERT="/etc/letsencrypt/live/${DOMAIN}/fullchain.pem"
RETRY_SECONDS="${CERTBOT_RETRY_SECONDS:-300}"
RENEW_INTERVAL="${CERTBOT_RENEW_INTERVAL:-43200}"

echo "Certbot: domain=${DOMAIN} email=${EMAIL}"

# Nginx must be up to answer the ACME webroot challenge
sleep 15

request_certificate() {
    certbot certonly --webroot \
        -w "$WEBROOT" \
        -d "$DOMAIN" \
        --email "$EMAIL" \
        --agree-tos \
        --non-interactive \
        --keep-until-expiring
}

if [ ! -f "$CERT" ]; then
    echo "Certbot: requesting initial certificate for ${DOMAIN}..."
    until request_certificate; do
        echo "Certbot: certificate request failed — retrying in ${RETRY_SECONDS}s (check DNS points to this server)"
        sleep "$RETRY_SECONDS"
    done
    echo "Certbot: initial certificate obtained"
fi

while true; do
    sleep "$RENEW_INTERVAL"
    if certbot renew --webroot -w "$WEBROOT" --quiet; then
        echo "Certbot: renewal check complete"
    fi
done
