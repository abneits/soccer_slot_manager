#!/bin/bash

# Docker Build Script for Soccer Slot Manager
# Usage: ./build.sh [version]

set -e  # Exit on error

# Configuration
IMAGE_NAME="soccer-slot-manager"
VERSION="${1:-latest}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo -e "${RED}❌ Error: Docker is not running${NC}"
    exit 1
fi

# Build image for local architecture
echo -e "${GREEN}📦 Building Docker image...${NC}"
echo "Image: ${IMAGE_NAME}:${VERSION}"
echo ""

docker build -t ${IMAGE_NAME}:${VERSION} .

# Also tag as latest if not already latest
if [ "$VERSION" != "latest" ]; then
    echo -e "${GREEN}🏷️  Tagging as latest...${NC}"
    docker tag ${IMAGE_NAME}:${VERSION} ${IMAGE_NAME}:latest
fi

echo ""
echo -e "${GREEN}✅ Build completed successfully${NC}"
echo ""

