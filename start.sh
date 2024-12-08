#!/bin/bash
set -e

echo "Starting all infrastructure services..."
docker-compose up --build -d postgres redis shortener pgadmin redis-commander
echo "All infrastructure services started."

echo "All services started successfully!"
