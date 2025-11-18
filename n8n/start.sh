#!/bin/bash

# Startup script for n8n on NAS

set -e

echo "Starting n8n automation service..."

# Check if .env file exists
if [ ! -f .env ]; then
    echo "Error: .env file not found!"
    echo "Please copy .env.example to .env and configure your settings:"
    echo "  cp .env.example .env"
    echo "  nano .env  # or use your preferred editor"
    exit 1
fi

# Create data directory structure
mkdir -p ../data/n8n/{data,db,files}
echo "✓ Created n8n data directory structure"

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
echo "Building n8n services..."
$DOCKER_COMPOSE build

echo "Starting n8n + PostgreSQL..."
$DOCKER_COMPOSE up -d

echo ""
echo "✓ n8n started successfully!"
echo ""
echo "Check status with: $DOCKER_COMPOSE ps"
echo "View logs with: $DOCKER_COMPOSE logs -f"
echo "Stop service with: $DOCKER_COMPOSE down"
echo ""
echo "Access n8n: http://localhost:5678"
