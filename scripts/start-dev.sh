#!/bin/bash
# Start development environment
# Last updated: 2025-08-30 22:40:55 UTC by nullroute-commits

set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}Starting development environment...${NC}"

# Copy environment file if it doesn't exist
if [ ! -f .env ]; then
    echo -e "${YELLOW}Creating .env file from example...${NC}"
    cp .env.example .env
fi

# Copy specific environment files
for env_file in .env.app .env.db .env.cache .env.queue .env.security .env.logging; do
    if [ ! -f "$env_file" ]; then
        echo -e "${YELLOW}Creating $env_file from example...${NC}"
        cp "${env_file}.example" "$env_file"
    fi
done

# Start services
echo -e "${YELLOW}Starting Docker services...${NC}"
docker-compose -f docker-compose.development.yml up -d

# Wait for services
echo -e "${YELLOW}Waiting for services to be ready...${NC}"
sleep 10

# Show status
echo -e "${GREEN}Development environment started!${NC}"
echo ""
echo -e "${YELLOW}Available services:${NC}"
echo "  🌐 Django App: http://localhost:8000"
echo "  📊 Admin Panel: http://localhost:8000/admin (admin/admin123)"
echo "  🗄️ Database Admin: http://localhost:8080"
echo "  🐰 RabbitMQ Management: http://localhost:15672 (guest/guest)"
echo "  📧 Mailhog: http://localhost:8025"
echo ""
echo -e "${YELLOW}Useful commands:${NC}"
echo "  View logs: docker-compose -f docker-compose.development.yml logs -f"
echo "  Stop services: docker-compose -f docker-compose.development.yml down"
echo "  Shell access: docker-compose -f docker-compose.development.yml exec web bash"