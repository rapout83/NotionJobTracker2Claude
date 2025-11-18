#!/bin/bash

# Stop script for n8n

set -e

echo "Stopping n8n automation service..."

# Determine docker compose command
if docker compose version &> /dev/null 2>&1; then
    DOCKER_COMPOSE="docker compose"
else
    DOCKER_COMPOSE="docker-compose"
fi

# Stop the service
$DOCKER_COMPOSE down

echo "✓ n8n stopped successfully!"
