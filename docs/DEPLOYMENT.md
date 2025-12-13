# Deployment Guide

This guide covers deployment procedures for all environments using our Docker Compose-based CI/CD pipeline.

## Table of Contents

1. [Overview](#overview)
2. [Prerequisites](#prerequisites)
3. [Environment Setup](#environment-setup)
4. [Deployment Strategies](#deployment-strategies)
5. [Step-by-Step Deployment](#step-by-step-deployment)
6. [Rollback Procedures](#rollback-procedures)
7. [Troubleshooting](#troubleshooting)

## Overview

Our deployment pipeline uses:
- **Docker Compose** for consistent environment management
- **Ansible** for orchestration and configuration management
- **PATH-scoped environment files** for secure configuration
- **Blue-green and rolling deployment** strategies

## Prerequisites

### Required Tools

- Docker Engine 27.2.0+
- Docker Compose v2.29.2+
- Ansible 10.5.0
- Access to target environment
- Proper credentials in vault

### Access Requirements

- SSH access to target servers
- Docker registry credentials
- Vault access for secrets
- Load balancer management access (production)

## Environment Setup

### 1. Load Environment Configuration

```bash
# Load environment with PATH scoping
source scripts/env-loader.sh [dev|test|staging|prod]

# Verify environment
echo $ENVIRONMENT
echo $PATH
```

### 2. Validate Configuration

```bash
# Validate environment files exist
ls -la environments/$ENVIRONMENT/

# Test environment loader
./scripts/env-loader.sh $ENVIRONMENT validate
```

### 3. Set Up Secrets

```bash
# Development/Test - use local .env files
cp environments/$ENVIRONMENT/.env.example environments/$ENVIRONMENT/.env.local

# Production - load from vault
vault kv get secret/enterprise-app/prod > /tmp/prod-secrets
source /tmp/prod-secrets
rm /tmp/prod-secrets
```

## Deployment Strategies

### Rolling Deployment (Default)

```yaml
# Gradual replacement of instances
deploy:
  strategy: rolling
  max_parallel: 1
  health_check_delay: 30s
```

### Blue-Green Deployment

```yaml
# Full environment swap
deploy:
  strategy: blue-green
  health_check_delay: 60s
  switch_delay: 30s
```

### Canary Deployment

```yaml
# Gradual traffic shift
deploy:
  strategy: canary
  initial_percentage: 10
  increment: 20
  delay_between_increments: 5m
```

## Step-by-Step Deployment

### 1. Pre-deployment Checks

```bash
# Check current version
make ps ENVIRONMENT=prod

# Verify health
curl https://api.example.com/health

# Create backup
ansible-playbook -i ansible/inventories/prod/hosts.yml \
  ansible/playbooks/backup.yml
```

### 2. Build and Test

```bash
# Run CI/CD pipeline
make pipeline ENVIRONMENT=staging

# Or manually:
make lint
make test
make build
make security
```

### 3. Deploy to Staging

```bash
# Using Make
make deploy ENVIRONMENT=staging

# Using Ansible directly
ansible-playbook -i ansible/inventories/staging/hosts.yml \
  ansible/playbooks/deploy.yml \
  -e "app_version=$(git rev-parse --short HEAD)" \
  -e "environment=staging"
```

### 4. Smoke Tests

```bash
# Automated smoke tests
pytest tests/smoke/ -v --environment=staging

# Manual verification
curl https://staging.example.com/api/v1/version
```

### 5. Deploy to Production

```bash
# Using environment script (recommended)
environments/prod/bin/deploy --confirm-production

# Using Make
make deploy ENVIRONMENT=prod

# Using Ansible with specific version
ansible-playbook -i ansible/inventories/prod/hosts.yml \
  ansible/playbooks/deploy.yml \
  -e "app_version=v1.2.3" \
  -e "environment=production" \
  -e "deployment_strategy=blue-green"
```

### 6. Post-deployment Verification

```bash
# Health checks
for i in {1..10}; do
  curl -s https://api.example.com/health | jq .
  sleep 5
done

# Check metrics
curl https://api.example.com/metrics | grep app_version

# Verify logs
docker compose -f docker-compose.prod.yml logs --tail 100
```

## Rollback Procedures

### Immediate Rollback

```bash
# Quick rollback to previous version
ansible-playbook -i ansible/inventories/prod/hosts.yml \
  ansible/playbooks/rollback.yml \
  -e "rollback_version=v1.2.2" \
  -e "environment=production" \
  -e "confirm_rollback=false"
```

### Rollback with Database Migration

```bash
# Rollback including database changes
ansible-playbook -i ansible/inventories/prod/hosts.yml \
  ansible/playbooks/rollback.yml \
  -e "rollback_version=v1.2.2" \
  -e "environment=production" \
  -e "rollback_migrations=true" \
  -e "rollback_migration=revision_hash"
```

### Emergency Rollback

```bash
# Fast rollback using Docker Compose
cd /opt/enterprise-app/config
docker compose down
APP_VERSION=v1.2.2 docker compose up -d
```

## Monitoring Deployment

### Real-time Monitoring

```bash
# Watch deployment progress
watch -n 2 'docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"'

# Monitor logs
docker compose logs -f app

# Check metrics
watch -n 5 'curl -s http://localhost:8000/metrics | grep -E "(up|version|requests)"'
```

### Grafana Dashboards

1. Access Grafana: https://grafana.example.com
2. Navigate to "Deployments" dashboard
3. Set time range to "Last 1 hour"
4. Monitor key metrics:
   - Request rate
   - Error rate
   - Response time
   - CPU/Memory usage

## Troubleshooting

### Common Issues

#### 1. Health Check Failures

```bash
# Check container logs
docker compose logs app --tail 100

# Test health endpoint directly
docker compose exec app curl localhost:8000/health

# Check database connection
docker compose exec app python -c "from src.core.database import engine; print(engine.url)"
```

#### 2. Migration Failures

```bash
# Check migration status
docker compose exec app alembic current

# Show migration history
docker compose exec app alembic history

# Manually run migrations
docker compose exec app alembic upgrade head
```

#### 3. Permission Issues

```bash
# Fix file permissions
sudo chown -R deploy:deploy /opt/enterprise-app

# Fix Docker socket permissions
sudo usermod -aG docker deploy
```

#### 4. Resource Constraints

```bash
# Check resource usage
docker stats

# Increase resources in docker-compose.yml
deploy:
  resources:
    limits:
      cpus: '2'
      memory: 2G
```

### Emergency Procedures

#### Complete Service Restart

```bash
# Stop all services
docker compose -f docker-compose.prod.yml down

# Clean up
docker system prune -f

# Start fresh
docker compose -f docker-compose.prod.yml up -d
```

#### Database Recovery

```bash
# Restore from backup
docker compose exec postgres pg_restore \
  -U postgres -d enterprise_prod \
  /backups/prod-backup-latest.sql

# Verify data integrity
docker compose exec app python scripts/verify_database.py
```

## Best Practices

1. **Always test in staging first**
2. **Create backups before deployment**
3. **Monitor metrics during deployment**
4. **Have rollback plan ready**
5. **Document any manual steps**
6. **Use version tags for production**
7. **Implement gradual rollouts**
8. **Verify health checks pass**

## Security Considerations

1. **Never commit secrets** - Use vault or environment files
2. **Rotate credentials regularly**
3. **Use read-only filesystem** where possible
4. **Implement network policies**
5. **Scan images before deployment**
6. **Use signed images** in production
7. **Implement RBAC** for deployment access

## Support

For deployment support:
- Slack: #deployments
- Email: devops@example.com
- On-call: See PagerDuty schedule