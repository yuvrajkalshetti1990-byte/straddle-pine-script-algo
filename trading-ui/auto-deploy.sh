#!/bin/bash

# Auto-deployment script for webhook or cron job
# This script can be triggered automatically when code is pushed to git

set -e

LOG_FILE="/var/log/trading-ui-deploy.log"

# Function to log with timestamp
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

log "🚀 Starting automatic deployment..."

# Navigate to the project directory
cd /opt/trading-platform || cd /root/trading-platform || cd ~/trading-platform || {
    log "❌ Cannot find project directory"
    exit 1
}

log "📁 Working in directory: $(pwd)"

# Check if we have any running containers first
if docker-compose ps -q | grep -q .; then
    log "📊 Current container status:"
    docker-compose ps | tee -a "$LOG_FILE"
fi

# Pull latest code from git
log "🔄 Pulling latest code from git..."
git pull origin main || git pull origin master || {
    log "❌ Git pull failed, trying to reset and pull..."
    git reset --hard HEAD
    git pull origin main || git pull origin master || {
        log "❌ Cannot pull latest code"
        exit 1
    }
}

# Stop existing containers
log "🛑 Stopping existing containers..."
docker-compose down

# Build images with no cache
log "🏗️ Building Docker images with no cache..."
docker-compose build --no-cache

# Start containers in detached mode
log "🚀 Starting containers in detached mode..."
docker-compose up -d

# Wait for containers to start
log "⏳ Waiting for containers to start..."
sleep 15

# Check container status
log "📊 Final container status:"
docker-compose ps | tee -a "$LOG_FILE"

# Health check
log "🔍 Testing application..."
if curl -f http://localhost:3000 >/dev/null 2>&1; then
    log "✅ Application is running successfully at https://cbamoon.com!"
else
    log "⚠️ Application might not be responding yet. Recent logs:"
    docker-compose logs --tail=10 trading-ui | tee -a "$LOG_FILE"
fi

# Clean up old images to save space
log "🧹 Cleaning up old Docker images..."
docker image prune -f >/dev/null 2>&1

log "🎉 Automatic deployment completed!"
log "🌐 Your app is live at: https://cbamoon.com"
log "=" | tr '=' '='| head -c 50 && echo

# Optional: Send notification (uncomment if you want notifications)
# curl -X POST -H 'Content-type: application/json' \
#     --data '{"text":"🚀 Trading UI deployed successfully at https://cbamoon.com!"}' \
#     YOUR_SLACK_WEBHOOK_URL