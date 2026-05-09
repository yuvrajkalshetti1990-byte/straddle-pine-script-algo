# VPS Deployment Guide for Trading UI

## Prerequisites

1. **VPS Requirements:**
   - Ubuntu 20.04+ or Debian 11+
   - 2GB RAM minimum (4GB recommended)
   - 20GB SSD storage minimum
   - Root or sudo access

2. **Domain Setup:**
   - Point cbamoon.com A record to your VPS IP
   - Point www.cbamoon.com CNAME to cbamoon.com

## Quick Deployment

### 1. Initial VPS Setup

```bash
# SSH into your VPS
ssh root@your-vps-ip

# Run the setup script
wget https://raw.githubusercontent.com/your-username/trading-platform/main/setup-vps.sh
chmod +x setup-vps.sh
./setup-vps.sh
```

### 2. Clone and Deploy

```bash
cd /opt/trading-platform
git clone https://github.com/your-username/trading-platform.git .

# Update the image name in docker-compose.override.yml
nano docker-compose.override.yml

# Start the application
docker-compose up -d
```

### 3. GitHub Secrets Setup

Add these secrets to your GitHub repository:

- `VPS_HOST`: Your VPS IP address
- `VPS_USERNAME`: SSH username (usually root)
- `VPS_SSH_KEY`: Your private SSH key for the VPS

## Configuration Files

### Docker Compose
- `docker-compose.yml`: Main services configuration
- `docker-compose.override.yml`: Production overrides

### Nginx
- `nginx.conf`: Nginx configuration with SSL and security headers
- Automatically configured for cbamoon.com domain

### SSL Certificates
- Automatic Let's Encrypt SSL certificates
- Auto-renewal configured via cron

## Management Commands

```bash
# View application logs
docker-compose logs -f trading-ui

# View nginx logs
docker-compose logs -f nginx

# Restart services
docker-compose restart

# Update application (triggers on git push)
docker-compose pull && docker-compose up -d

# Manual deployment
git pull origin main
docker-compose up -d --build

# Health check
curl https://cbamoon.com/health
```

## Monitoring

### Health Checks
- Automatic health monitoring every 5 minutes
- Container restart on failure
- Application health endpoint: `/health`

### Logs
- Application logs: `/var/log/docker/`
- Nginx logs: `/var/log/nginx/`
- Log rotation configured automatically

## Security Features

- SSL/TLS encryption with Let's Encrypt
- Security headers configured
- Rate limiting for API endpoints
- Firewall configured (UFW)
- Regular security updates

## Troubleshooting

### Common Issues

1. **Port 80/443 already in use:**
   ```bash
   sudo systemctl stop apache2
   sudo systemctl disable apache2
   ```

2. **SSL certificate issues:**
   ```bash
   certbot renew --dry-run
   ```

3. **Application not responding:**
   ```bash
   docker-compose restart trading-ui
   ```

4. **Check container status:**
   ```bash
   docker-compose ps
   docker-compose logs trading-ui
   ```

### Performance Optimization

1. **Enable Nginx caching:**
   - Static files cached for 1 year
   - Gzip compression enabled

2. **Docker optimization:**
   - Multi-stage builds reduce image size
   - Health checks ensure reliability

3. **System optimization:**
   - Log rotation prevents disk filling
   - Automatic container restart on failure

## Backup Strategy

```bash
# Backup application data
docker-compose exec trading-ui npm run backup

# Backup configuration
tar -czf backup-$(date +%Y%m%d).tar.gz /opt/trading-platform
```

## Support

For deployment issues:
1. Check logs: `docker-compose logs`
2. Verify domain DNS settings
3. Check SSL certificate status: `certbot certificates`
4. Ensure firewall allows HTTP/HTTPS: `ufw status`