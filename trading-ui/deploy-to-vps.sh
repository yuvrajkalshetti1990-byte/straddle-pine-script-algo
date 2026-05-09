#!/bin/bash

echo "🚀 Starting simple deployment on VPS..."

# Navigate to the project directory
cd /opt/trading-platform || cd /root/trading-platform || cd ~/trading-platform || {
    echo "❌ Cannot find project directory. Please navigate to your cloned repository."
    echo "Available directories:"
    ls -la ~/
    ls -la /opt/ 2>/dev/null || true
    exit 1
}

echo "📁 Current directory: $(pwd)"
echo "📋 Files in directory:"
ls -la

# Pull latest code from git
echo "🔄 Pulling latest code from git..."
git pull origin main || git pull origin master || {
    echo "❌ Git pull failed, trying to reset and pull..."
    git reset --hard HEAD
    git pull origin main || git pull origin master || {
        echo "❌ Cannot pull latest code. Check git repository status."
        exit 1
    }
}

# Stop existing containers
echo "🛑 Stopping existing containers..."
docker-compose down

# Build images with no cache
echo "🏗️ Building Docker images with no cache..."
docker-compose build --no-cache

# Start containers in detached mode
echo "🚀 Starting containers in detached mode..."
docker-compose up -d

# Wait for containers to start
echo "⏳ Waiting for containers to start..."
sleep 15

# Check container status
echo "📊 Container status:"
docker-compose ps

# Check if application is running
echo "🔍 Testing application..."
if curl -f http://localhost:3000 2>/dev/null || curl -f http://localhost:3000/health 2>/dev/null; then
    echo "✅ Application is running successfully!"
    echo "🌐 Your app is live at: https://cbamoon.com"
    echo "🔗 Local access: http://$(curl -s ifconfig.me 2>/dev/null || echo 'YOUR-VPS-IP'):3000"
else
    echo "⚠️ Application might not be responding yet. Checking logs..."
    docker-compose logs --tail=20 trading-ui
fi

# Clean up old images to save space
echo "🧹 Cleaning up old Docker images..."
docker image prune -f

echo ""
echo "🎉 Deployment completed!"
echo "📝 Useful commands:"
echo "- View logs: docker-compose logs -f"
echo "- Restart: docker-compose restart"
echo "- Stop: docker-compose down"
echo "- Redeploy: ./deploy-to-vps.sh"
echo ""
    build:
      context: .
      dockerfile: Dockerfile
    environment:
      - NODE_ENV=production
      - PORT=3000
      - NEXT_TELEMETRY_DISABLED=1
    restart: unless-stopped
    logging:
      driver: json-file
      options:
        max-size: "10m"
        max-file: "3"

  nginx:
    restart: unless-stopped
    logging:
      driver: json-file
      options:
        max-size: "10m"
        max-file: "3"
EOF

# Build and start the application
echo "🏗️ Building Docker images..."
docker-compose build --no-cache

echo "🚀 Starting application..."
docker-compose up -d

# Wait for containers to start
sleep 10

# Check container status
echo "📊 Container status:"
docker-compose ps

# Check if application is running
echo "🔍 Testing application..."
if curl -f http://localhost:3000/health 2>/dev/null || curl -f http://localhost:3000 2>/dev/null; then
    echo "✅ Application is running successfully!"
    echo "🌐 Access your app at: http://72.60.202.180:3000"
else
    echo "❌ Application might not be responding. Checking logs..."
    docker-compose logs trading-ui
fi

# Show logs
echo "📋 Recent logs:"
docker-compose logs --tail=20 trading-ui

echo ""
echo "🎉 Deployment completed!"
echo "📝 Next steps:"
echo "1. Test your app at: http://72.60.202.180:3000"
echo "2. Configure domain name pointing to 72.60.202.180"
echo "3. Set up SSL with: certbot --nginx -d cbamoon.com"
echo ""
echo "🔧 Management commands:"
echo "- View logs: docker-compose logs -f"
echo "- Restart: docker-compose restart"
echo "- Stop: docker-compose down"
echo "- Update: docker-compose pull && docker-compose up -d"