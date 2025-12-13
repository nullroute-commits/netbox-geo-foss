#!/bin/bash
# Development entrypoint script
# Last updated: 2025-08-30 22:40:55 UTC by nullroute-commits

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}Starting Django development server...${NC}"

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

# Create superuser if it doesn't exist
echo -e "${YELLOW}Creating superuser...${NC}"
python manage.py shell -c "
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin', 'admin@example.com', 'admin123')
    print('Superuser created: admin/admin123')
else:
    print('Superuser already exists')
" || echo -e "${YELLOW}Superuser creation skipped${NC}"

# Collect static files
echo -e "${YELLOW}Collecting static files...${NC}"
python manage.py collectstatic --noinput || echo -e "${YELLOW}Static files collection skipped${NC}"

# Create logs directory
mkdir -p /app/logs
touch /app/logs/django.log
touch /app/logs/audit.log

echo -e "${GREEN}Development setup complete!${NC}"
echo -e "${GREEN}Admin panel: http://localhost:8000/admin/${NC}"
echo -e "${GREEN}Username: admin${NC}"
echo -e "${GREEN}Password: admin123${NC}"

# Execute the main command
exec "$@"