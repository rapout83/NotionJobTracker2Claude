#!/bin/bash

# Startup script for NotionJobTracker2Claude on NAS

set -e

echo "Starting NotionJobTracker2Claude webhook service..."

# Check if .env file exists
if [ ! -f .env ]; then
    echo "Error: .env file not found!"
    echo "Please copy .env.example to .env and configure your API keys:"
    echo "  cp .env.example .env"
    echo "  nano .env  # or use your preferred editor"
    exit 1
fi

# Create webhook logs directory
mkdir -p webhook/logs
echo "✓ Created webhook directory structure"

# Check Docker and Docker Compose
if ! command -v docker &> /dev/null; then
    echo "Error: Docker is not installed or not in PATH"
    exit 1
fi

if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
    echo "Error: Docker Compose is not installed or not in PATH"
    exit 1
fi

# Determine docker compose command
if docker compose version &> /dev/null; then
    DOCKER_COMPOSE="docker compose"
else
    DOCKER_COMPOSE="docker-compose"
fi

# Build and start the service
echo "Building Docker image..."
$DOCKER_COMPOSE build

echo "Starting service..."
$DOCKER_COMPOSE up -d

echo ""
echo "Service started successfully!"
echo ""
echo "Check status with: $DOCKER_COMPOSE ps"
echo "View logs with: $DOCKER_COMPOSE logs -f"
echo "Stop service with: $DOCKER_COMPOSE down"
echo ""
echo "Webhook endpoint: http://localhost:${PORT:-8000}/webhook/notion"
echo "Health check: http://localhost:${PORT:-8000}/health"
