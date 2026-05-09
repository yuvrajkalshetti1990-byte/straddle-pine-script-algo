#!/bin/bash

# VPS Deployment Script for Trading UI
# This script sets up the production environment on your VPS

set -e

echo "🚀 Setting up Trading UI on VPS..."

# Update system
echo "📦 Updating system packages..."
apt-get update && apt-get upgrade -y

# Install Docker and Docker Compose if not installed
if ! command -v docker &> /dev/null; then
    echo "🐳 Installing Docker..."
    curl -fsSL https://get.docker.com -o get-docker.sh
    sh get-docker.sh
    usermod -aG docker $USER
fi

if ! command -v docker-compose &> /dev/null; then
    echo "🔧 Installing Docker Compose..."
    curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    chmod +x /usr/local/bin/docker-compose
fi

# Install Nginx (for SSL/domain setup)
if ! command -v nginx &> /dev/null; then
    echo "🌐 Installing Nginx..."
    apt-get install -y nginx
fi

# Install Certbot for SSL certificates
if ! command -v certbot &> /dev/null; then
    echo "🔒 Installing Certbot..."
    apt-get install -y certbot python3-certbot-nginx
fi

# Create application directory
APP_DIR="/opt/trading-platform"
mkdir -p $APP_DIR
cd $APP_DIR

# Create SSL directory
mkdir -p ssl

# Generate SSL certificates for cbamoon.com
echo "🔒 Setting up SSL certificates..."
certbot --nginx -d cbamoon.com -d www.cbamoon.com --non-interactive --agree-tos --email admin@cbamoon.com

# Copy certificates to our ssl directory
cp /etc/letsencrypt/live/cbamoon.com/fullchain.pem ssl/cbamoon.com.crt
cp /etc/letsencrypt/live/cbamoon.com/privkey.pem ssl/cbamoon.com.key

# Set up auto-renewal for SSL certificates
echo "0 12 * * * /usr/bin/certbot renew --quiet" | crontab -

# Create docker-compose override for production
cat > docker-compose.override.yml << EOF
version: '3.8'

services:
  trading-ui:
    image: ghcr.io/your-username/trading-platform:latest
    environment:
      - NODE_ENV=production
      - PORT=3000
    restart: always
    logging:
      driver: json-file
      options:
        max-size: "10m"
        max-file: "3"

  nginx:
    volumes:
      - /etc/letsencrypt/live/cbamoon.com/fullchain.pem:/etc/nginx/ssl/cbamoon.com.crt:ro
      - /etc/letsencrypt/live/cbamoon.com/privkey.pem:/etc/nginx/ssl/cbamoon.com.key:ro
    restart: always
    logging:
      driver: json-file
      options:
        max-size: "10m"
        max-file: "3"
EOF

# Set up log rotation
cat > /etc/logrotate.d/trading-ui << EOF
/var/log/nginx/*.log {
    daily
    missingok
    rotate 14
    compress
    delaycompress
    notifempty
    create 0644 www-data www-data
    prerotate
        if [ -d /etc/logrotate.d/httpd-prerotate ]; then \
            run-parts /etc/logrotate.d/httpd-prerotate; \
        fi \
    endprerotate
    postrotate
        invoke-rc.d nginx rotate >/dev/null 2>&1
    endpostrotate
}
EOF

# Set up firewall
echo "🔥 Configuring firewall..."
ufw allow ssh
ufw allow 'Nginx Full'
ufw --force enable

# Create systemd service for monitoring
cat > /etc/systemd/system/trading-ui-monitor.service << EOF
[Unit]
Description=Trading UI Health Monitor
After=docker.service

[Service]
Type=oneshot
ExecStart=/opt/trading-platform/health-check.sh

[Timer]
OnCalendar=*:0/5
Persistent=true

[Install]
WantedBy=timers.target
EOF

# Create health check script
cat > health-check.sh << EOF
#!/bin/bash
cd /opt/trading-platform

# Check if containers are running
if ! docker-compose ps | grep -q "Up"; then
    echo "Containers not running, attempting restart..."
    docker-compose up -d
    sleep 30
fi

# Check application health
if ! curl -f http://localhost:3000/health; then
    echo "Application health check failed, restarting..."
    docker-compose restart trading-ui
fi
EOF

chmod +x health-check.sh

# Enable and start the health monitor
systemctl daemon-reload
systemctl enable trading-ui-monitor.timer
systemctl start trading-ui-monitor.timer

echo "✅ VPS setup completed!"
echo "📝 Next steps:"
echo "1. Clone your repository to $APP_DIR"
echo "2. Update the docker-compose.override.yml with your actual image name"
echo "3. Run 'docker-compose up -d' to start the application"
echo "4. Your site will be available at https://cbamoon.com"
echo ""
echo "🔧 Useful commands:"
echo "- View logs: docker-compose logs -f"
echo "- Restart services: docker-compose restart"
echo "- Update application: docker-compose pull && docker-compose up -d"