#!/bin/bash

# Configuration
COMPOSE_FILE="docker-compose.yml"
BACKEND_IMAGE="pm-a-backend-backend"
FRONTEND_IMAGE="pm-a-backend-frontend"

echo "🚀 Starting AgileFlow Docker Management Script..."

# 1. Build images
echo "🛠️ Building Docker images with Buildx..."
docker buildx bake --file $COMPOSE_FILE --load

# 2. Run Docker Scout Audit
if docker scout version >/dev/null 2>&1; then
    echo "🔍 Running Docker Scout Security Audit..."
    echo "--- Backend Audit ---"
    docker scout quickview $BACKEND_IMAGE
    echo "--- Frontend Audit ---"
    docker scout quickview $FRONTEND_IMAGE
else
    echo "⚠️ Docker Scout not found. Skipping security audit."
fi

# 3. Start services
echo "✅ Starting services in detached mode..."
docker-compose -f $COMPOSE_FILE up -d

echo "📊 Status:"
docker-compose -f $COMPOSE_FILE ps

echo "🎉 AgileFlow is running!"
echo "Frontend: http://localhost:3000"
echo "Backend:  http://localhost:8000"
