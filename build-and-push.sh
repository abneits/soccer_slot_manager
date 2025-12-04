#!/bin/bash

# Docker Build and Push Script for Soccer Slot Manager (ARM64)
# Usage: ./build-and-push.sh [version]

set -e  # Exit on error

# Configuration
DOCKER_USERNAME="${DOCKER_USERNAME:-abneits}"
IMAGE_NAME="soccer-slot-manager"
VERSION="${1:-latest}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}🐳 Docker Build and Push Script (ARM64)${NC}"
echo "=================================="
echo ""

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo -e "${RED}❌ Error: Docker is not running${NC}"
    exit 1
fi

# Check if logged in to Docker Hub
if ! docker info | grep -q "Username"; then
    echo -e "${YELLOW}⚠️  Not logged in to Docker Hub${NC}"
    echo "Please run: docker login"
    exit 1
fi

# Setup QEMU for ARM64 emulation
echo -e "${GREEN}🔧 Setting up QEMU for ARM64 emulation...${NC}"
docker run --rm --privileged multiarch/qemu-user-static --reset -p yes

# Build image for ARM64 using buildkit
echo -e "${GREEN}📦 Building Docker image for ARM64...${NC}"
echo "Image: ${DOCKER_USERNAME}/${IMAGE_NAME}:${VERSION}"
echo ""

DOCKER_BUILDKIT=1 docker build --platform linux/arm64 -t ${DOCKER_USERNAME}/${IMAGE_NAME}:${VERSION} .

# Also tag as latest if not already latest
if [ "$VERSION" != "latest" ]; then
    echo -e "${GREEN}🏷️  Tagging as latest...${NC}"
    docker tag ${DOCKER_USERNAME}/${IMAGE_NAME}:${VERSION} ${DOCKER_USERNAME}/${IMAGE_NAME}:latest
fi

echo ""
echo -e "${GREEN}✅ Build completed successfully${NC}"
echo ""

# Push to Docker Hub
echo -e "${GREEN}📤 Pushing to Docker Hub...${NC}"
echo ""

docker push ${DOCKER_USERNAME}/${IMAGE_NAME}:${VERSION}

if [ "$VERSION" != "latest" ]; then
    docker push ${DOCKER_USERNAME}/${IMAGE_NAME}:latest
fi

echo ""
echo -e "${GREEN}✅ Push completed successfully${NC}"
echo ""
echo "=================================="
echo -e "${GREEN}🎉 Docker image published!${NC}"
echo ""
echo "Image: ${DOCKER_USERNAME}/${IMAGE_NAME}:${VERSION}"
echo ""
echo "To pull and run on ARM64 device:"
echo "  docker pull ${DOCKER_USERNAME}/${IMAGE_NAME}:${VERSION}"
echo "  docker run -p 8000:8000 -e MONGO_URI='your-mongo-uri' ${DOCKER_USERNAME}/${IMAGE_NAME}:${VERSION}"
echo ""
