#!/usr/bin/env bash
set -e

# Wait for DB to start
sleep 5
echo "Initializing database..."
docker exec -i db psql -U postgres -d shortener < services/shortener/schema.sql
echo "Database initialized."
