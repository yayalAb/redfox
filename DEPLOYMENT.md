# Odoo 18 Deployment on Ubuntu with Docker and Nginx

This guide walks you through deploying Odoo 18 on Ubuntu using Docker Compose and Nginx as a reverse proxy.

## Prerequisites

- **Ubuntu 22.04 or 24.04** (or similar Debian-based distro)
- **Docker** 24+ and **Docker Compose** v2+
- **4GB RAM minimum** (8GB+ recommended for production)
- **2 vCPUs minimum** (4+ recommended for production)

## 1. Install Docker on Ubuntu

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Docker
sudo apt install -y ca-certificates curl gnupg
sudo install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
sudo chmod a+r /etc/apt/keyrings/docker.gpg

echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

sudo apt update
sudo apt install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

# Add your user to docker group (logout/login required)
sudo usermod -aG docker $USER
```

## 2. Configure Environment

```bash
# Copy the example env file
cp .env.example .env

# Edit with your values (use a strong password for production!)
nano .env
```

**Important variables:**
- `POSTGRES_PASSWORD` — Use a strong, unique password (must match for both PostgreSQL and Odoo)
- Edit `config/odoo.conf` and set `admin_passwd` to a strong master password for Odoo database creation

## 3. Deploy with Docker Compose

```bash
# Start all services (Odoo, PostgreSQL, Nginx)
docker compose up -d

# Check status
docker compose ps
```

Odoo will be available at:
- **With Nginx:** `http://your-domain` or `http://localhost` (port 80)
- **Direct (no Nginx):** `http://localhost:8069`

## 4. SSL with Let's Encrypt (Production)

For HTTPS in production:

```bash
# Install certbot
sudo apt install -y certbot python3-certbot-nginx

# Get certificate (replace with your domain)
sudo certbot --nginx -d odoo.example.com

# Certbot will modify Nginx config automatically
# Renewal is automatic via systemd timer
```

## 5. Custom Addons

To use custom Odoo modules (e.g., from your `addons` folder):

1. Create the folder and place your modules:
   ```bash
   mkdir -p addons
   # Copy your custom modules into addons/
   ```
3. Restart Odoo:
   ```bash
   docker compose restart odoo
   ```
4. In Odoo: **Apps → Update Apps List**, then install your modules.

## 6. Useful Commands

```bash
# View logs
docker compose logs -f odoo

# Stop all services
docker compose down

# Stop and remove volumes (⚠️ deletes all data!)
docker compose down -v

# Restart Odoo only
docker compose restart odoo

# Backup database
docker compose exec db pg_dump -U odoo postgres > backup_$(date +%Y%m%d).sql

# Restore database
cat backup_20250101.sql | docker compose exec -T db psql -U odoo postgres
```

## 7. Architecture Overview

```
Internet → Nginx (port 80/443) → Odoo (port 8069)
                                    ↓
                              PostgreSQL (port 5432)
```

- **Nginx:** Reverse proxy, SSL termination, static file caching
- **Odoo:** Application server
- **PostgreSQL:** Database (not exposed to the internet)

## 8. Troubleshooting

| Issue | Solution |
|-------|----------|
| Odoo won't start | Check `docker compose logs odoo` — often DB connection (wrong password or DB not ready) |
| 502 Bad Gateway | Odoo container may still be starting; wait 1–2 min or check `docker compose ps` |
| Can't create database | Ensure `admin_passwd` in `config/odoo.conf` is set and PostgreSQL password in `.env` is correct |
| Custom addons not visible | Verify volume mount and folder structure; check Odoo logs |

## 9. Security Checklist (Production)

- [ ] Change all default passwords in `.env`
- [ ] Enable SSL (Let's Encrypt)
- [ ] Set `proxy_mode = True` in Odoo config when behind Nginx
- [ ] Restrict PostgreSQL to internal Docker network only (default)
- [ ] Configure firewall: `sudo ufw allow 80,443/tcp && sudo ufw enable`
- [ ] Set up automated backups
- [ ] Use `web.base.url` in Odoo System Parameters if URL differs from host
