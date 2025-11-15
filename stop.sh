#!/bin/bash

# Stop script for NotionJobTracker2Claude

set -e

echo "Stopping NotionJobTracker2Claude webhook service..."

# Determine docker compose command
if docker compose version &> /dev/null 2>&1; then
    DOCKER_COMPOSE="docker compose"
else
    DOCKER_COMPOSE="docker-compose"
fi

# Stop the service
$DOCKER_COMPOSE down

echo "Service stopped successfully!"
