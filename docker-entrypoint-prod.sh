#!/bin/bash
# Production entrypoint script
# Last updated: 2025-08-30 22:40:55 UTC by nullroute-commits

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}Starting Django production server...${NC}"

# Wait for database to be ready
echo -e "${YELLOW}Waiting for database...${NC}"
while ! nc -z ${POSTGRES_HOST:-db} ${POSTGRES_PORT:-5432}; do
  sleep 1
done
echo -e "${GREEN}Database is ready!${NC}"

# Wait for memcached to be ready
echo -e "${YELLOW}Waiting for memcached...${NC}"
while ! nc -z ${MEMCACHED_SERVERS%%:*} ${MEMCACHED_SERVERS##*:}; do
  sleep 1
done
echo -e "${GREEN}Memcached is ready!${NC}"

# Wait for RabbitMQ to be ready
echo -e "${YELLOW}Waiting for RabbitMQ...${NC}"
while ! nc -z ${RABBITMQ_HOST:-rabbitmq} ${RABBITMQ_PORT:-5672}; do
  sleep 1
done
echo -e "${GREEN}RabbitMQ is ready!${NC}"

# Run database migrations
echo -e "${YELLOW}Running database migrations...${NC}"
python manage.py migrate --noinput

# Collect static files
echo -e "${YELLOW}Collecting static files...${NC}"
python manage.py collectstatic --noinput

# Create logs directory with proper permissions
mkdir -p /app/logs
touch /app/logs/django.log
touch /app/logs/audit.log
touch /app/logs/error.log

# Health check
echo -e "${YELLOW}Performing health check...${NC}"
python -c "
import django
django.setup()
from django.db import connection
cursor = connection.cursor()
cursor.execute('SELECT 1')
print('Database connection: OK')
"

echo -e "${GREEN}Production environment ready!${NC}"

# Execute the main command
exec "$@"