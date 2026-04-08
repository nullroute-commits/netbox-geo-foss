# Database Design Documentation

This document describes the database design for the Django 5 Multi-Architecture CI/CD Pipeline application.

**Last updated:** 2025-08-30 22:40:55 UTC by nullroute-commits

## Table of Contents

- [Overview](#overview)
- [Database Technology](#database-technology)
- [Schema Design](#schema-design)
- [Core Models](#core-models)
- [Relationships](#relationships)
- [Indexing Strategy](#indexing-strategy)
- [Performance Optimization](#performance-optimization)
- [Security Considerations](#security-considerations)
- [Backup and Recovery](#backup-and-recovery)

## Overview

The application uses PostgreSQL 17.2 as the primary database with SQLAlchemy 1.4.49 as the ORM layer. The database design follows best practices for security, performance, and maintainability.

### Key Features

- **ACID Compliance:** Full transactional integrity
- **UUID Primary Keys:** For security and distributed systems
- **Audit Trail:** Comprehensive change tracking
- **RBAC Support:** Role-based access control
- **Performance Optimized:** Proper indexing and query optimization
- **Multi-tenant Ready:** Designed for scalability

## Database Technology

### PostgreSQL Configuration

```yaml
# docker-compose.production.yml
services:
  db:
    image: postgres:17.2
    command: >
      postgres
      -c max_connections=200
      -c shared_buffers=512MB
      -c work_mem=8MB
      -c maintenance_work_mem=128MB
      -c effective_cache_size=2GB
      -c wal_buffers=32MB
      -c checkpoint_completion_target=0.9
      -c random_page_cost=1.1
```

### Performance Settings

| Setting | Development | Testing | Production |
|---------|-------------|---------|------------|
| max_connections | 100 | 50 | 200 |
| shared_buffers | 256MB | 128MB | 512MB |
| work_mem | 4MB | 2MB | 8MB |
| effective_cache_size | 1GB | 512MB | 2GB |

## Schema Design

### Entity Relationship Diagram

```sql
                    ┌─────────────────────────────┐
                    │         Users               │
                    │─────────────────────────────│
                    │ id (UUID) [PK]              │
                    │ username (VARCHAR)          │
                    │ email (VARCHAR)             │
                    │ password_hash (VARCHAR)     │
                    │ first_name (VARCHAR)        │
                    │ last_name (VARCHAR)         │
                    │ is_active (BOOLEAN)         │
                    │ is_staff (BOOLEAN)          │
                    │ is_superuser (BOOLEAN)      │
                    │ last_login (TIMESTAMP)      │
                    │ date_joined (TIMESTAMP)     │
                    │ created_at (TIMESTAMP)      │
                    │ updated_at (TIMESTAMP)      │
                    │ created_by (UUID) [FK]      │
                    │ updated_by (UUID) [FK]      │
                    └─────────────────────────────┘
                              │
                              │ (Many-to-Many)
                              │
                    ┌─────────────────────────────┐
                    │       user_roles            │
                    │─────────────────────────────│
                    │ user_id (UUID) [FK]         │
                    │ role_id (UUID) [FK]         │
                    └─────────────────────────────┘
                              │
                              │
                    ┌─────────────────────────────┐
                    │         Roles               │
                    │─────────────────────────────│
                    │ id (UUID) [PK]              │
                    │ name (VARCHAR)              │
                    │ description (TEXT)          │
                    │ is_active (BOOLEAN)         │
                    │ is_system (BOOLEAN)         │
                    │ created_at (TIMESTAMP)      │
                    │ updated_at (TIMESTAMP)      │
                    │ created_by (UUID) [FK]      │
                    │ updated_by (UUID) [FK]      │
                    └─────────────────────────────┘
                              │
                              │ (Many-to-Many)
                              │
                    ┌─────────────────────────────┐
                    │    role_permissions         │
                    │─────────────────────────────│
                    │ role_id (UUID) [FK]         │
                    │ permission_id (UUID) [FK]   │
                    └─────────────────────────────┘
                              │
                              │
                    ┌─────────────────────────────┐
                    │      Permissions            │
                    │─────────────────────────────│
                    │ id (UUID) [PK]              │
                    │ name (VARCHAR)              │
                    │ description (TEXT)          │
                    │ resource (VARCHAR)          │
                    │ action (VARCHAR)            │
                    │ is_active (BOOLEAN)         │
                    │ is_system (BOOLEAN)         │
                    │ created_at (TIMESTAMP)      │
                    │ updated_at (TIMESTAMP)      │
                    │ created_by (UUID) [FK]      │
                    │ updated_by (UUID) [FK]      │
                    └─────────────────────────────┘

    ┌─────────────────────────────────────────────────────────────────┐
    │                        AuditLog                                │
    │─────────────────────────────────────────────────────────────────│
    │ id (UUID) [PK]                                                 │
    │ user_id (UUID) [FK] → Users.id                                 │
    │ session_id (VARCHAR)                                           │
    │ ip_address (VARCHAR)                                           │
    │ user_agent (TEXT)                                              │
    │ action (VARCHAR)                                               │
    │ resource_type (VARCHAR)                                        │
    │ resource_id (UUID)                                             │
    │ resource_repr (VARCHAR)                                        │
    │ old_values (JSONB)                                             │
    │ new_values (JSONB)                                             │
    │ request_method (VARCHAR)                                       │
    │ request_path (VARCHAR)                                         │
    │ request_data (JSONB)                                           │
    │ response_status (INTEGER)                                      │
    │ metadata (JSONB)                                               │
    │ message (TEXT)                                                 │
    │ created_at (TIMESTAMP)                                         │
    │ updated_at (TIMESTAMP)                                         │
    │ created_by (UUID) [FK]                                         │
    │ updated_by (UUID) [FK]                                         │
    └─────────────────────────────────────────────────────────────────┘

    ┌─────────────────────────────────────────────────────────────────┐
    │                   SystemConfiguration                          │
    │─────────────────────────────────────────────────────────────────│
    │ id (UUID) [PK]                                                 │
    │ key (VARCHAR) [UNIQUE]                                         │
    │ value (JSONB)                                                  │
    │ description (TEXT)                                             │
    │ is_active (BOOLEAN)                                            │
    │ is_system (BOOLEAN)                                            │
    │ created_at (TIMESTAMP)                                         │
    │ updated_at (TIMESTAMP)                                         │
    │ created_by (UUID) [FK]                                         │
    │ updated_by (UUID) [FK]                                         │
    └─────────────────────────────────────────────────────────────────┘
```

## Core Models

### Users Table

```sql
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    username VARCHAR(150) UNIQUE NOT NULL,
    email VARCHAR(254) UNIQUE NOT NULL,
    password_hash VARCHAR(128) NOT NULL,
    first_name VARCHAR(150) NOT NULL,
    last_name VARCHAR(150) NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    is_staff BOOLEAN NOT NULL DEFAULT FALSE,
    is_superuser BOOLEAN NOT NULL DEFAULT FALSE,
    last_login TIMESTAMP WITH TIME ZONE,
    date_joined TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    created_by UUID REFERENCES users(id),
    updated_by UUID REFERENCES users(id)
);

-- Indexes
CREATE INDEX idx_users_username ON users(username);
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_is_active ON users(is_active);
CREATE INDEX idx_users_created_at ON users(created_at);
```

### Roles Table

```sql
CREATE TABLE roles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(100) UNIQUE NOT NULL,
    description TEXT,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    is_system BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    created_by UUID REFERENCES users(id),
    updated_by UUID REFERENCES users(id)
);

-- Indexes
CREATE INDEX idx_roles_name ON roles(name);
CREATE INDEX idx_roles_is_active ON roles(is_active);
CREATE INDEX idx_roles_is_system ON roles(is_system);
```

### Permissions Table

```sql
CREATE TABLE permissions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(100) UNIQUE NOT NULL,
    description TEXT,
    resource VARCHAR(100) NOT NULL,
    action VARCHAR(50) NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    is_system BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    created_by UUID REFERENCES users(id),
    updated_by UUID REFERENCES users(id),
    
    CONSTRAINT unique_resource_action UNIQUE(resource, action)
);

-- Indexes
CREATE INDEX idx_permissions_name ON permissions(name);
CREATE INDEX idx_permissions_resource ON permissions(resource);
CREATE INDEX idx_permissions_action ON permissions(action);
CREATE INDEX idx_permissions_is_active ON permissions(is_active);
```

### Association Tables

```sql
-- User-Role Many-to-Many
CREATE TABLE user_roles (
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    role_id UUID NOT NULL REFERENCES roles(id) ON DELETE CASCADE,
    PRIMARY KEY (user_id, role_id)
);

CREATE INDEX idx_user_roles_user_id ON user_roles(user_id);
CREATE INDEX idx_user_roles_role_id ON user_roles(role_id);

-- Role-Permission Many-to-Many
CREATE TABLE role_permissions (
    role_id UUID NOT NULL REFERENCES roles(id) ON DELETE CASCADE,
    permission_id UUID NOT NULL REFERENCES permissions(id) ON DELETE CASCADE,
    PRIMARY KEY (role_id, permission_id)
);

CREATE INDEX idx_role_permissions_role_id ON role_permissions(role_id);
CREATE INDEX idx_role_permissions_permission_id ON role_permissions(permission_id);
```

### Audit Log Table

```sql
CREATE TABLE audit_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id),
    session_id VARCHAR(40),
    ip_address VARCHAR(45),
    user_agent TEXT,
    action VARCHAR(50) NOT NULL,
    resource_type VARCHAR(100),
    resource_id UUID,
    resource_repr VARCHAR(255),
    old_values JSONB,
    new_values JSONB,
    request_method VARCHAR(10),
    request_path VARCHAR(255),
    request_data JSONB,
    response_status INTEGER,
    metadata JSONB,
    message TEXT,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    created_by UUID REFERENCES users(id),
    updated_by UUID REFERENCES users(id)
);

-- Indexes for audit logs
CREATE INDEX idx_audit_logs_user_id ON audit_logs(user_id);
CREATE INDEX idx_audit_logs_action ON audit_logs(action);
CREATE INDEX idx_audit_logs_resource_type ON audit_logs(resource_type);
CREATE INDEX idx_audit_logs_resource_id ON audit_logs(resource_id);
CREATE INDEX idx_audit_logs_created_at ON audit_logs(created_at);
CREATE INDEX idx_audit_logs_session_id ON audit_logs(session_id);
CREATE INDEX idx_audit_logs_ip_address ON audit_logs(ip_address);

-- GIN indexes for JSONB columns
CREATE INDEX idx_audit_logs_old_values_gin ON audit_logs USING GIN(old_values);
CREATE INDEX idx_audit_logs_new_values_gin ON audit_logs USING GIN(new_values);
CREATE INDEX idx_audit_logs_request_data_gin ON audit_logs USING GIN(request_data);
CREATE INDEX idx_audit_logs_metadata_gin ON audit_logs USING GIN(metadata);
```

### System Configuration Table

```sql
CREATE TABLE system_configurations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    key VARCHAR(100) UNIQUE NOT NULL,
    value JSONB,
    description TEXT,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    is_system BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    created_by UUID REFERENCES users(id),
    updated_by UUID REFERENCES users(id)
);

-- Indexes
CREATE INDEX idx_system_configurations_key ON system_configurations(key);
CREATE INDEX idx_system_configurations_is_active ON system_configurations(is_active);
CREATE INDEX idx_system_configurations_is_system ON system_configurations(is_system);
CREATE INDEX idx_system_configurations_value_gin ON system_configurations USING GIN(value);
```

## Relationships

### RBAC Relationships

```
Users ←→ user_roles ←→ Roles ←→ role_permissions ←→ Permissions

1. A User can have multiple Roles (Many-to-Many)
2. A Role can have multiple Permissions (Many-to-Many)
3. A User inherits all Permissions from their assigned Roles
4. Superusers bypass all permission checks
```

### Audit Relationships

```
Users → AuditLog (One-to-Many)
- Every audit log entry is associated with a user (nullable for system actions)
- Users can have multiple audit log entries
- Audit logs track changes to all entities
```

### Self-Referencing Relationships

```
Users → Users (created_by, updated_by)
Roles → Users (created_by, updated_by)
Permissions → Users (created_by, updated_by)
AuditLog → Users (created_by, updated_by)
SystemConfiguration → Users (created_by, updated_by)
```

## Indexing Strategy

### Primary Indexes

```sql
-- Primary Keys (Automatic)
users(id)
roles(id)
permissions(id)
audit_logs(id)
system_configurations(id)

-- Unique Constraints
users(username)
users(email)
roles(name)
permissions(name)
permissions(resource, action) -- Composite
system_configurations(key)
```

### Performance Indexes

```sql
-- User lookups
CREATE INDEX idx_users_username_active ON users(username) WHERE is_active = TRUE;
CREATE INDEX idx_users_email_active ON users(email) WHERE is_active = TRUE;

-- Role-based queries
CREATE INDEX idx_user_roles_composite ON user_roles(user_id, role_id);
CREATE INDEX idx_role_permissions_composite ON role_permissions(role_id, permission_id);

-- Audit queries
CREATE INDEX idx_audit_logs_user_action ON audit_logs(user_id, action);
CREATE INDEX idx_audit_logs_resource ON audit_logs(resource_type, resource_id);
CREATE INDEX idx_audit_logs_created_at_desc ON audit_logs(created_at DESC);

-- Time-based partitioning preparation
CREATE INDEX idx_audit_logs_created_month ON audit_logs(DATE_TRUNC('month', created_at));
```

### JSONB Indexes

```sql
-- GIN indexes for JSONB searching
CREATE INDEX idx_audit_logs_old_values_gin ON audit_logs USING GIN(old_values);
CREATE INDEX idx_audit_logs_new_values_gin ON audit_logs USING GIN(new_values);
CREATE INDEX idx_audit_logs_metadata_gin ON audit_logs USING GIN(metadata);
CREATE INDEX idx_system_configurations_value_gin ON system_configurations USING GIN(value);

-- Specific JSONB path indexes
CREATE INDEX idx_audit_logs_metadata_ip ON audit_logs USING GIN((metadata->'ip_address'));
CREATE INDEX idx_system_configurations_value_type ON system_configurations USING GIN((value->'type'));
```

## Performance Optimization

### Query Optimization

```sql
-- Efficient permission checking
-- Instead of: Multiple joins and subqueries
-- Use: Materialized view or cached results

CREATE MATERIALIZED VIEW user_permissions_mv AS
SELECT 
    u.id as user_id,
    u.username,
    ARRAY_AGG(DISTINCT p.name) as permissions
FROM users u
JOIN user_roles ur ON u.id = ur.user_id
JOIN roles r ON ur.role_id = r.id
JOIN role_permissions rp ON r.id = rp.role_id
JOIN permissions p ON rp.permission_id = p.id
WHERE u.is_active = TRUE 
  AND r.is_active = TRUE 
  AND p.is_active = TRUE
GROUP BY u.id, u.username;

-- Refresh strategy
CREATE OR REPLACE FUNCTION refresh_user_permissions_mv()
RETURNS TRIGGER AS $$
BEGIN
    REFRESH MATERIALIZED VIEW CONCURRENTLY user_permissions_mv;
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

-- Triggers for automatic refresh
CREATE TRIGGER refresh_user_permissions_trigger
    AFTER INSERT OR UPDATE OR DELETE ON user_roles
    FOR EACH STATEMENT EXECUTE FUNCTION refresh_user_permissions_mv();
```

### Partitioning Strategy

```sql
-- Partition audit_logs by month for better performance
CREATE TABLE audit_logs_partitioned (
    LIKE audit_logs INCLUDING ALL
) PARTITION BY RANGE (created_at);

-- Monthly partitions
CREATE TABLE audit_logs_y2025m01 PARTITION OF audit_logs_partitioned
    FOR VALUES FROM ('2025-01-01') TO ('2025-02-01');

CREATE TABLE audit_logs_y2025m02 PARTITION OF audit_logs_partitioned
    FOR VALUES FROM ('2025-02-01') TO ('2025-03-01');
-- ... continue for each month

-- Automatic partition creation
CREATE OR REPLACE FUNCTION create_monthly_audit_partition()
RETURNS VOID AS $$
DECLARE
    start_date DATE;
    end_date DATE;
    table_name TEXT;
BEGIN
    start_date := DATE_TRUNC('month', CURRENT_DATE + INTERVAL '1 month');
    end_date := start_date + INTERVAL '1 month';
    table_name := 'audit_logs_y' || TO_CHAR(start_date, 'YYYY') || 'm' || TO_CHAR(start_date, 'MM');
    
    EXECUTE format('CREATE TABLE IF NOT EXISTS %I PARTITION OF audit_logs_partitioned 
                    FOR VALUES FROM (%L) TO (%L)', 
                   table_name, start_date, end_date);
END;
$$ LANGUAGE plpgsql;
```

### Connection Pooling

```python
# SQLAlchemy configuration
DATABASE_CONFIG = {
    'poolclass': QueuePool,
    'pool_size': 20,
    'max_overflow': 30,
    'pool_timeout': 30,
    'pool_recycle': 3600,
    'pool_pre_ping': True,
}
```

## Security Considerations

### Data Protection

```sql
-- Row-level security example
ALTER TABLE users ENABLE ROW LEVEL SECURITY;

-- Users can only see their own data unless they're staff
CREATE POLICY user_isolation ON users
    FOR ALL TO app_role
    USING (id = current_setting('app.current_user_id')::UUID OR 
           current_setting('app.user_is_staff')::BOOLEAN = TRUE);

-- Audit logs are read-only for regular users
CREATE POLICY audit_read_only ON audit_logs
    FOR SELECT TO app_role
    USING (user_id = current_setting('app.current_user_id')::UUID OR 
           current_setting('app.user_is_staff')::BOOLEAN = TRUE);
```

### Encryption

```sql
-- Sensitive data encryption
CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- Function to encrypt sensitive data
CREATE OR REPLACE FUNCTION encrypt_sensitive_data(data TEXT)
RETURNS TEXT AS $$
BEGIN
    RETURN pgp_sym_encrypt(data, current_setting('app.encryption_key'));
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Function to decrypt sensitive data
CREATE OR REPLACE FUNCTION decrypt_sensitive_data(encrypted_data TEXT)
RETURNS TEXT AS $$
BEGIN
    RETURN pgp_sym_decrypt(encrypted_data, current_setting('app.encryption_key'));
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;
```

### Access Control

```sql
-- Database roles
CREATE ROLE app_readonly;
CREATE ROLE app_readwrite;
CREATE ROLE app_admin;

-- Grant appropriate permissions
GRANT SELECT ON ALL TABLES IN SCHEMA public TO app_readonly;
GRANT SELECT, INSERT, UPDATE ON ALL TABLES IN SCHEMA public TO app_readwrite;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO app_admin;

-- Application-specific user
CREATE USER django_app WITH PASSWORD 'secure_password';
GRANT app_readwrite TO django_app;
```

## Backup and Recovery

### Backup Strategy

```bash
#!/bin/bash
# backup-database.sh

# Full backup
pg_dump -h $DB_HOST -U $DB_USER -d $DB_NAME -Fc > backup_$(date +%Y%m%d_%H%M%S).dump

# Schema-only backup
pg_dump -h $DB_HOST -U $DB_USER -d $DB_NAME -s > schema_$(date +%Y%m%d_%H%M%S).sql

# Data-only backup
pg_dump -h $DB_HOST -U $DB_USER -d $DB_NAME -a > data_$(date +%Y%m%d_%H%M%S).sql

# Incremental backup using WAL-E or similar
wal-e backup-push /var/lib/postgresql/data
```

### Recovery Procedures

```sql
-- Point-in-time recovery
SELECT pg_create_restore_point('before_major_update');

-- Restore from backup
pg_restore -h $DB_HOST -U $DB_USER -d $DB_NAME -c backup_20250830_220000.dump

-- Verify data integrity
SELECT COUNT(*) FROM users;
SELECT COUNT(*) FROM audit_logs WHERE created_at > NOW() - INTERVAL '1 day';
```

### Monitoring Queries

```sql
-- Database size monitoring
SELECT 
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size
FROM pg_tables 
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;

-- Index usage monitoring
SELECT 
    schemaname,
    tablename,
    indexname,
    idx_tup_read,
    idx_tup_fetch
FROM pg_stat_user_indexes 
ORDER BY idx_tup_read DESC;

-- Query performance monitoring
SELECT 
    query,
    calls,
    total_time,
    mean_time,
    rows
FROM pg_stat_statements 
ORDER BY total_time DESC 
LIMIT 10;
```

---

This database design provides a solid foundation for the Django application with proper security, performance optimization, and maintainability considerations built in from the ground up.