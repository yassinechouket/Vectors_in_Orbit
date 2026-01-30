#!/bin/bash
# Build and push Docker images to Docker Hub
# Usage: ./docker-push.sh <dockerhub_username>

set -e

DOCKERHUB_USERNAME=${1:-fincommerce}
VERSION=${2:-latest}

echo "🐳 Building and pushing Docker images..."
echo "   Username: $DOCKERHUB_USERNAME"
echo "   Version: $VERSION"
echo ""

# Build backend
echo "📦 Building backend image..."
docker build -t $DOCKERHUB_USERNAME/fincommerce-backend:$VERSION ./backend
docker tag $DOCKERHUB_USERNAME/fincommerce-backend:$VERSION $DOCKERHUB_USERNAME/fincommerce-backend:latest

# Build frontend
echo "📦 Building frontend image..."
docker build -t $DOCKERHUB_USERNAME/fincommerce-frontend:$VERSION ./Web_app
docker tag $DOCKERHUB_USERNAME/fincommerce-frontend:$VERSION $DOCKERHUB_USERNAME/fincommerce-frontend:latest

# Push to Docker Hub
echo "🚀 Pushing to Docker Hub..."
echo "   (Make sure you're logged in: docker login)"
echo ""

docker push $DOCKERHUB_USERNAME/fincommerce-backend:$VERSION
docker push $DOCKERHUB_USERNAME/fincommerce-backend:latest
docker push $DOCKERHUB_USERNAME/fincommerce-frontend:$VERSION
docker push $DOCKERHUB_USERNAME/fincommerce-frontend:latest

echo ""
echo "✅ Done! Images pushed to Docker Hub:"
echo "   - $DOCKERHUB_USERNAME/fincommerce-backend:$VERSION"
echo "   - $DOCKERHUB_USERNAME/fincommerce-frontend:$VERSION"
echo ""
echo "📋 To pull and run on another machine:"
echo "   docker pull $DOCKERHUB_USERNAME/fincommerce-backend:latest"
echo "   docker pull $DOCKERHUB_USERNAME/fincommerce-frontend:latest"
