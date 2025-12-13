# NetBox Geographic Data Integration - System Architecture

**Last updated:** 2025-12-13  
**Version:** 1.0.0  
**Python:** 3.13.1

## Table of Contents

- [Overview](#overview)
- [System Components](#system-components)
- [Data Flow](#data-flow)
- [API Integration Patterns](#api-integration-patterns)
- [Performance Considerations](#performance-considerations)
- [Security Model](#security-model)
- [Deployment Architecture](#deployment-architecture)

## Overview

NetBox Geo FOSS implements a modular architecture for integrating geographic data from multiple FOSS sources (GeoNames, Natural Earth, OpenStreetMap) into NetBox. The system is optimized for bulk operations, enterprise-grade reliability, and network automation workflows.

### Design Principles

- **Modularity**: Pluggable importers for each data source
- **Reliability**: Retry logic, rate limiting, comprehensive error handling
- **Performance**: Bulk operations, caching, async support
- **Type Safety**: Full type hints with Pydantic v2 validation
- **Observability**: Structured logging with context

## System Components

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                         Geographic Data Sources                      │
│                                                                      │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐           │
│  │  GeoNames    │    │ Natural Earth│    │ OpenStreetMap│           │
│  │    API       │    │   Downloads  │    │ Nominatim API│           │
│  └──────────────┘    └──────────────┘    └──────────────┘           │
└─────────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      NetBox Geo Application                          │
│                                                                      │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │                         CLI Interface                          │ │
│  │  (Click 8.1.8 + Rich 13.9.4 for terminal UI)                  │ │
│  └────────────────────────────────────────────────────────────────┘ │
│                                │                                     │
│  ┌─────────────────┬──────────┴──────────┬─────────────────┐       │
│  │                 │                      │                  │       │
│  │   Importers     │    Core Services     │   NetBox Client │       │
│  │                 │                      │                  │       │
│  │  ┌───────────┐  │  ┌──────────────┐   │  ┌───────────┐  │       │
│  │  │ GeoNames  │  │  │ Config Mgmt  │   │  │ API Client│  │       │
│  │  │ Importer  │  │  │ (Pydantic v2)│   │  │           │  │       │
│  │  └───────────┘  │  └──────────────┘   │  └───────────┘  │       │
│  │                 │                      │        │         │       │
│  │  ┌───────────┐  │  ┌──────────────┐   │        │         │       │
│  │  │   NatEarth│  │  │ Validation   │   │  ┌─────▼──────┐ │       │
│  │  │ Importer  │  │  │  Engine      │   │  │Rate Limiter│ │       │
│  │  └───────────┘  │  └──────────────┘   │  └────────────┘ │       │
│  │                 │                      │        │         │       │
│  │  ┌───────────┐  │  ┌──────────────┐   │  ┌─────▼──────┐ │       │
│  │  │    OSM    │  │  │   Logging    │   │  │Retry Logic │ │       │
│  │  │ Importer  │  │  │  (Loguru)    │   │  └────────────┘ │       │
│  │  └───────────┘  │  └──────────────┘   │                  │       │
│  └─────────────────┴─────────────────────┴─────────────────┘       │
│                                │                                     │
│  ┌────────────────────────────┴──────────────────────────────────┐ │
│  │                      Cache & Database Layer                    │ │
│  │  ┌────────────┐  ┌────────────┐  ┌────────────┐               │ │
│  │  │ PostgreSQL │  │   Redis    │  │ File Cache │               │ │
│  │  │  (Metadata)│  │  (Session) │  │(Geo Data)  │               │ │
│  │  └────────────┘  └────────────┘  └────────────┘               │ │
│  └────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────────┐
│                         NetBox Instance                              │
│                                                                      │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │                      NetBox API (4.4.8+)                      │ │
│  │  • Countries  • Regions  • Cities  • Locations                 │ │
│  └────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────┘
```

### Core Modules

#### 1. Configuration Management (`core/config.py`)

```python
AppSettings
├── NetBoxConfig          # NetBox API settings
├── DataSourceConfig      # Geographic data source URLs
├── DataManagementConfig  # Batch sizes, update intervals
└── PerformanceConfig     # Rate limits, worker threads
```

- **Technology**: Pydantic v2 with Settings management
- **Features**: Environment variable loading, validation, nested configs
- **Pattern**: Singleton pattern for global settings

#### 2. NetBox Client (`netbox/client.py`)

```python
NetBoxClient
├── _create_client()      # Initialize pynetbox
├── _retry_with_backoff() # Exponential backoff retry
├── get()                 # GET requests
├── create()              # POST single object
├── bulk_create()         # POST multiple objects
├── update()              # PATCH object
└── delete()              # DELETE object
```

- **Technology**: pynetbox 7.5.0
- **Features**: Rate limiting, retry logic, bulk operations
- **Pattern**: Decorator pattern for rate limiting

#### 3. Rate Limiter (`netbox/rate_limiter.py`)

```python
RateLimiter (Token Bucket Algorithm)
├── __init__()            # Configure tokens/minute
├── _refill()             # Refill tokens over time
├── acquire()             # Consume tokens
└── __enter__/__exit__()  # Context manager support
```

- **Algorithm**: Token bucket
- **Features**: Blocking/non-blocking modes, thread-safe
- **Pattern**: Context manager pattern

#### 4. Data Importers (`importers/`)

```python
BaseImporter (Abstract)
├── fetch_data()          # Download from source
├── transform_data()      # Transform to NetBox format
├── validate_data()       # Validate with Pydantic
└── import_to_netbox()    # Bulk create in NetBox

GeoNamesImporter extends BaseImporter
NaturalEarthImporter extends BaseImporter
OSMImporter extends BaseImporter
```

- **Pattern**: Template method pattern
- **Features**: Pluggable, reusable, testable

#### 5. CLI Interface (`cli/main.py`)

```python
CLI Commands
├── import-data           # Import from sources
├── sync                  # Sync with NetBox
├── validate              # Validate data
└── config                # Configuration management
```

- **Technology**: Click 8.1.8 + Rich 13.9.4
- **Features**: Color output, progress bars, tables
- **Pattern**: Command pattern

## Data Flow

### Import Workflow

```
1. User Command
   │
   ▼
2. CLI Parser (Click)
   │
   ▼
3. Load Configuration (Pydantic)
   │
   ▼
4. Initialize Importer
   │
   ▼
5. Fetch Data from Source
   │  (HTTP/File Download)
   ▼
6. Transform to Standard Format
   │  (Pandas/GeoPandas)
   ▼
7. Validate Data
   │  (Pydantic Models)
   ▼
8. Cache Locally
   │  (PostgreSQL/File)
   ▼
9. Rate Limit Check
   │
   ▼
10. Bulk Create in NetBox
    │  (pynetbox)
    ▼
11. Log Results
    │  (Loguru)
    ▼
12. Return Summary
```

### Sync Workflow

```
1. User Command
   │
   ▼
2. Load Cached Data
   │
   ▼
3. Fetch NetBox Current State
   │  (Rate Limited)
   ▼
4. Compare & Diff
   │
   ▼
5. Generate Change Set
   │
   ▼
6. Apply Changes
   │  (Create/Update/Delete)
   ▼
7. Verify Results
   │
   ▼
8. Update Cache
```

## API Integration Patterns

### NetBox API Client Pattern

```python
# Rate-limited, auto-retry client
with NetBoxClient(config) as client:
    # Automatically handles:
    # - Rate limiting (100 calls/min default)
    # - Retry with exponential backoff
    # - Error handling and logging
    countries = client.bulk_create(
        endpoint="dcim.regions",
        data=country_data
    )
```

### Batch Processing Pattern

```python
def process_in_batches(
    data: list[dict],
    batch_size: int = 1000
) -> list[dict]:
    """Process large datasets in manageable batches."""
    results = []
    for batch in chunked(data, batch_size):
        validated = [validate_record(r) for r in batch]
        created = client.bulk_create(validated)
        results.extend(created)
    return results
```

## Performance Considerations

### Optimization Strategies

1. **Bulk Operations**
   - Batch size: 1000 records (configurable)
   - Parallel processing with worker threads
   - Async support for I/O operations

2. **Caching**
   - PostgreSQL for metadata
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                           Application Layer                                 │
│                                                                             │
│  ┌───────────────┐  ┌───────────────┐  ┌───────────────┐  ┌───────────────┐ │
│  │ Django App #1 │  │ Django App #2 │  │ Django App #3 │  │ Django App #N │ │
│  │ (Gunicorn)    │  │ (Gunicorn)    │  │ (Gunicorn)    │  │ (Gunicorn)    │ │
│  │               │  │               │  │               │  │               │ │
│  │ • RBAC        │  │ • RBAC        │  │ • RBAC        │  │ • RBAC        │ │
│  │ • Audit       │  │ • Audit       │  │ • Audit       │  │ • Audit       │ │
│  │ • Business    │  │ • Business    │  │ • Business    │  │ • Business    │ │
│  │   Logic       │  │   Logic       │  │   Logic       │  │   Logic       │ │
│  └───────────────┘  └───────────────┘  └───────────────┘  └───────────────┘ │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                              Data Layer                                     │
│                                                                             │
│  ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────────────┐ │
│  │  PostgreSQL 17  │    │   Memcached     │    │      RabbitMQ 3.12      │ │
│  │                 │    │     1.6.22      │    │                         │ │
│  │ • Primary DB    │    │                 │    │ • Message Broker        │ │
│  │ • Transactions  │    │ • Session Cache │    │ • Task Queues           │ │
│  │ • ACID Compliance│   │ • Query Cache   │    │ • Event Streaming       │ │
│  │ • Backup/Recovery│   │ • User Cache    │    │ • Dead Letter Queues    │ │
│  │ • Replication   │    │ • App Cache     │    │ • Priority Queues       │ │
│  └─────────────────┘    └─────────────────┘    └─────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Network Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              DMZ Network                                    │
│                            (Public Subnet)                                 │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────────┐ │
│  │                        Load Balancer                                    │ │
│  │                     (Nginx - Port 80/443)                              │ │
│  └─────────────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼ (Internal Network)
┌─────────────────────────────────────────────────────────────────────────────┐
│                           Application Network                               │
│                            (Private Subnet)                                │
│                                                                             │
│  ┌───────────────┐  ┌───────────────┐  ┌───────────────┐  ┌───────────────┐ │
│  │ Django:8000   │  │ Django:8000   │  │ Django:8000   │  │ Django:8000   │ │
│  └───────────────┘  └───────────────┘  └───────────────┘  └───────────────┘ │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼ (Database Network)
┌─────────────────────────────────────────────────────────────────────────────┐
│                             Data Network                                   │
│                            (Private Subnet)                                │
│                                                                             │
│  ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────────────┐ │
│  │ PostgreSQL:5432 │    │ Memcached:11211 │    │   RabbitMQ:5672/15672   │ │
│  └─────────────────┘    └─────────────────┘    └─────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Component Architecture

### Django Application Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           Django Application                               │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────────┐ │
│  │                         Presentation Layer                              │ │
│  │                                                                         │ │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────────┐ │ │
│  │  │   Views     │  │  Templates  │  │   Forms     │  │   Static Files  │ │ │
│  │  │ (REST API)  │  │   (HTML)    │  │ (Validation)│  │   (CSS/JS)      │ │ │
│  │  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────────┘ │ │
│  └─────────────────────────────────────────────────────────────────────────┘ │
│                                      │                                       │
│  ┌─────────────────────────────────────────────────────────────────────────┐ │
│  │                         Business Logic Layer                            │ │
│  │                                                                         │ │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────────┐ │ │
│  │  │   Services  │  │   RBAC      │  │   Audit     │  │   Utilities     │ │ │
│  │  │ (Business)  │  │  (Access)   │  │ (Logging)   │  │   (Helpers)     │ │ │
│  │  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────────┘ │ │
│  └─────────────────────────────────────────────────────────────────────────┘ │
│                                      │                                       │
│  ┌─────────────────────────────────────────────────────────────────────────┐ │
│  │                         Data Access Layer                               │ │
│  │                                                                         │ │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────────┐ │ │
│  │  │   Models    │  │   ORM       │  │   Cache     │  │   Queue         │ │ │
│  │  │ (Django)    │  │(SQLAlchemy) │  │(Memcached)  │  │  (RabbitMQ)     │ │ │
│  │  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────────┘ │ │
│  └─────────────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────────┘
```

### RBAC Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              RBAC System                                   │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────────┐ │
│  │                         Permission Layer                                │ │
│  │                                                                         │ │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────────┐ │ │
│  │  │@require_    │  │@require_    │  │@require_any_│  │   Permission    │ │ │
│  │  │permission   │  │role         │  │permission   │  │   Checking      │ │ │
│  │  │(decorator)  │  │(decorator)  │  │(decorator)  │  │   (Runtime)     │ │ │
│  │  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────────┘ │ │
│  └─────────────────────────────────────────────────────────────────────────┘ │
│                                      │                                       │
│  ┌─────────────────────────────────────────────────────────────────────────┐ │
│  │                           Cache Layer                                   │ │
│  │                                                                         │ │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────────┐ │ │
│  │  │   User      │  │   Role      │  │ Permission  │  │   Session       │ │ │
│  │  │ Permissions │  │ Permissions │  │   Cache     │  │    Cache        │ │ │
│  │  │   Cache     │  │   Cache     │  │ (Memcached) │  │  (Memcached)    │ │ │
│  │  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────────┘ │ │
│  └─────────────────────────────────────────────────────────────────────────┘ │
│                                      │                                       │
│  ┌─────────────────────────────────────────────────────────────────────────┐ │
│  │                           Data Layer                                    │ │
│  │                                                                         │ │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────────┐ │ │
│  │  │    User     │◄─┤ user_roles  ├─►│    Role     │  │   Permission    │ │ │
│  │  │   Model     │  │   (M2M)     │  │   Model     │◄─┤    Model        │ │ │
│  │  │             │  │             │  │             │  │ role_permissions│ │ │
│  │  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────────┘ │ │
│  └─────────────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Audit System Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                            Audit System                                    │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────────┐ │
│  │                         Collection Layer                                │ │
│  │                                                                         │ │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────────┐ │ │
│  │  │   Model     │  │   Request   │  │    Auth     │  │    Manual       │ │ │
│  │  │  Changes    │  │  Logging    │  │  Logging    │  │   Logging       │ │ │
│  │  │(Automatic)  │  │(Middleware) │  │(Signals)    │  │ (@audit_activity│ │ │
│  │  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────────┘ │ │
│  └─────────────────────────────────────────────────────────────────────────┘ │
│                                      │                                       │
│  ┌─────────────────────────────────────────────────────────────────────────┐ │
│  │                        Processing Layer                                 │ │
│  │                                                                         │ │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────────┐ │ │
│  │  │   Data      │  │   Field     │  │   Context   │  │   Correlation   │ │ │
│  │  │Sanitization │  │ Validation  │  │ Enhancement │  │     (IDs)       │ │ │
│  │  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────────┘ │ │
│  └─────────────────────────────────────────────────────────────────────────┘ │
│                                      │                                       │
│  ┌─────────────────────────────────────────────────────────────────────────┐ │
│  │                         Storage Layer                                   │ │
│  │                                                                         │ │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────────┐ │ │
│  │  │  AuditLog   │  │    File     │  │  External   │  │    Archive      │ │ │
│  │  │  (Database) │  │   Logging   │  │   Systems   │  │   Storage       │ │ │
│  │  │             │  │   (JSON)    │  │   (Sentry)  │  │   (S3/GCS)      │ │ │
│  │  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────────┘ │ │
│  └─────────────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Data Architecture

### Database Schema Overview

```sql
-- Core Entity Relationship Diagram

┌─────────────────┐    ┌─────────────────┐    ┌─────────────────────────────┐
│      Users      │    │      Roles      │    │       Permissions           │
│─────────────────│    │─────────────────│    │─────────────────────────────│
│ • id (UUID)     │    │ • id (UUID)     │    │ • id (UUID)                 │
│ • username      │◄─┐ │ • name          │    │ • name                      │
│ • email         │  │ │ • description   │    │ • description               │
│ • password_hash │  │ │ • is_active     │    │ • resource                  │
│ • first_name    │  │ │ • is_system     │    │ • action                    │
│ • last_name     │  │ │ • created_at    │    │ • is_active                 │
│ • is_active     │  │ │ • updated_at    │    │ • is_system                 │
│ • is_staff      │  │ └─────────────────┘    │ • created_at                │
│ • is_superuser  │  │          │              │ • updated_at                │
│ • last_login    │  │          │              └─────────────────────────────┘
│ • date_joined   │  │          │                           ▲
│ • created_at    │  │          │                           │
│ • updated_at    │  │          └─────────┐                 │
└─────────────────┘  │                    │                 │
          │           │    ┌─────────────────┐              │
          │           └────┤   user_roles    │              │
          │                │─────────────────│              │
          │                │ • user_id (FK)  │              │
          │                │ • role_id (FK)  │              │
          │                └─────────────────┘              │
          │                          │                      │
          │                          │                      │
          │                          ▼                      │
          │                ┌─────────────────┐              │
          │                │ role_permissions│              │
          │                │─────────────────│              │
          │                │ • role_id (FK)  │──────────────┘
          │                │ • permission_id │
          │                └─────────────────┘
          │
          │
          ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                              AuditLog                                      │
│─────────────────────────────────────────────────────────────────────────────│
│ • id (UUID)              • request_method          • metadata (JSONB)       │
│ • user_id (FK)           • request_path            • message               │
│ • session_id             • request_data (JSONB)    • created_at            │
│ • ip_address             • response_status         • updated_at            │
│ • user_agent             • old_values (JSONB)                              │
│ • action                 • new_values (JSONB)                              │
│ • resource_type          • resource_id                                     │
│ • resource_repr          • created_by                                      │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Data Flow Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                            Data Flow Diagram                               │
│                                                                             │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐   │
│  │   Client    │───▶│   Nginx     │───▶│   Django    │───▶│ PostgreSQL  │   │
│  │  Request    │    │Load Balancer│    │Application  │    │  Database   │   │
│  └─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘   │
│                                               │                             │
│                                               ▼                             │
│                                      ┌─────────────┐                        │
│                                      │  Memcached  │                        │
│                                      │    Cache    │                        │
│                                      └─────────────┘                        │
│                                               │                             │
│                                               ▼                             │
│                                      ┌─────────────┐                        │
│                                      │  RabbitMQ   │                        │
│                                      │Message Queue│                        │
│                                      └─────────────┘                        │
│                                               │                             │
│                                               ▼                             │
│                                      ┌─────────────┐                        │
│                                      │ Background  │                        │
│                                      │   Workers   │                        │
│                                      └─────────────┘                        │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Security Architecture

### Security Layers

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           Security Architecture                             │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────────┐ │
│  │                         Network Security                                │ │
│  │                                                                         │ │
│  │  • Firewall Rules                 • DDoS Protection                     │ │
│  │  • WAF (Web Application Firewall) • Network Segmentation               │ │
│  │  • Rate Limiting                  • VPN Access                         │ │
│  │  • SSL/TLS Termination            • Private Subnets                    │ │
│  └─────────────────────────────────────────────────────────────────────────┘ │
│                                      │                                       │
│  ┌─────────────────────────────────────────────────────────────────────────┐ │
│  │                       Application Security                              │ │
│  │                                                                         │ │
│  │  • RBAC Authorization             • Input Validation                    │ │
│  │  • JWT/Session Authentication     • Output Encoding                    │ │
│  │  • CSRF Protection               • SQL Injection Prevention            │ │
│  │  • XSS Protection                • Path Traversal Prevention           │ │
│  │  • Security Headers              • File Upload Security                │ │
│  └─────────────────────────────────────────────────────────────────────────┘ │
│                                      │                                       │
│  ┌─────────────────────────────────────────────────────────────────────────┐ │
│  │                          Data Security                                  │ │
│  │                                                                         │ │
│  │  • Encryption at Rest             • Data Masking                       │ │
│  │  • Encryption in Transit          • Access Logging                     │ │
│  │  • Database Security              • Backup Encryption                  │ │
│  │  • Field-Level Encryption         • Key Management                     │ │
│  └─────────────────────────────────────────────────────────────────────────┘ │
│                                      │                                       │
│  ┌─────────────────────────────────────────────────────────────────────────┐ │
│  │                       Infrastructure Security                           │ │
│  │                                                                         │ │
│  │  • Container Security             • Secrets Management                  │ │
│  │  • Image Scanning                 • Environment Isolation              │ │
│  │  • Runtime Protection             • Monitoring & Alerting              │ │
│  │  • Vulnerability Scanning         • Incident Response                  │ │
│  └─────────────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Authentication & Authorization Flow

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                     Authentication & Authorization Flow                     │
│                                                                             │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐   │
│  │   Client    │───▶│   Login     │───▶│   Session   │───▶│   RBAC      │   │
│  │  Request    │    │ Endpoint    │    │ Creation    │    │   Check     │   │
│  └─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘   │
│                             │                    │                │         │
│                             ▼                    ▼                ▼         │
│                    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐   │
│                    │   Audit     │    │   Cache     │    │ Permission  │   │
│                    │  Logging    │    │ Session     │    │  Validation │   │
│                    └─────────────┘    └─────────────┘    └─────────────┘   │
│                                                                 │           │
│                                                                 ▼           │
│                                                        ┌─────────────┐     │
│                                                        │   Resource  │     │
│                                                        │   Access    │     │
│                                                        └─────────────┘     │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Deployment Architecture

### Multi-Environment Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          Development Environment                            │
│                                                                             │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐ │
│  │   Django    │  │ PostgreSQL  │  │ Memcached   │  │      RabbitMQ       │ │
│  │ (Debug=True)│  │   (Local)   │  │  (Local)    │  │      (Local)        │ │
│  │   Port:8000 │  │ Port:5432   │  │ Port:11211  │  │  Port:5672/15672    │ │
│  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────────────┘ │
│                                                                             │
│  Additional Services:                                                       │
│  • Adminer (Database Admin)          • Mailhog (Email Testing)             │
│  • Debug Toolbar                     • Live Reload                         │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│                            Testing Environment                              │
│                                                                             │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐ │
│  │   Django    │  │ PostgreSQL  │  │ Memcached   │  │      RabbitMQ       │ │
│  │(Debug=False)│  │  (tmpfs)    │  │ (In-Memory) │  │     (Ephemeral)     │ │
│  │  Test Mode  │  │  Fast I/O   │  │   Testing   │  │     Test Queues     │ │
│  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────────────┘ │
│                                                                             │
│  Test Services:                                                             │
│  • Parallel Test Runners             • Coverage Reporting                  │
│  • Code Quality Checks               • Security Scanning                   │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│                           Production Environment                            │
│                                                                             │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐ │
│  │   Nginx     │  │   Django    │  │ PostgreSQL  │  │      Memcached      │ │
│  │Load Balancer│  │  (Scaled)   │  │(Optimized)  │  │     (Clustered)     │ │
│  │ Port:80/443 │  │   Multiple  │  │   Master/   │  │   High Available    │ │
│  └─────────────┘  │  Instances  │  │   Replica   │  │     Distributed     │ │
│                   └─────────────┘  └─────────────┘  └─────────────────────┘ │
│                                                                             │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐ │
│  │  RabbitMQ   │  │ Monitoring  │  │   Logging   │  │      Backup         │ │
│  │ (Clustered) │  │(Prometheus) │  │ (Fluentd)   │  │   (Automated)       │ │
│  │ Persistent  │  │  Grafana    │  │  Central    │  │    S3/GCS           │ │
│  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────────┘
```

### CI/CD Pipeline Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              CI/CD Pipeline                                │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────────┐ │
│  │                         Source Control                                  │ │
│  │                                                                         │ │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────────┐ │ │
│  │  │   GitHub    │  │   Feature   │  │   Main      │  │    Release      │ │ │
│  │  │ Repository  │  │   Branch    │  │   Branch    │  │    Branch       │ │ │
│  │  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────────┘ │ │
│  └─────────────────────────────────────────────────────────────────────────┘ │
│                                      │                                       │
│  ┌─────────────────────────────────────────────────────────────────────────┐ │
│  │                         Build Pipeline                                  │ │
│  │                                                                         │ │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────────┐ │ │
│  │  │    Lint     │  │    Test     │  │   Build     │  │    Security     │ │ │
│  │  │  (Quality)  │  │(Unit/Int)   │  │ (Docker)    │  │   Scanning      │ │ │
│  │  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────────┘ │ │
│  └─────────────────────────────────────────────────────────────────────────┘ │
│                                      │                                       │
│  ┌─────────────────────────────────────────────────────────────────────────┐ │
│  │                       Deployment Pipeline                               │ │
│  │                                                                         │ │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────────┐ │ │
│  │  │   Stage     │  │    Test     │  │ Production  │  │   Monitoring    │ │ │
│  │  │Environment  │  │Environment  │  │Environment  │  │   & Alerting    │ │ │
│  │  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────────┘ │ │
│  └─────────────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Performance Architecture

### Performance Optimization Strategy

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         Performance Architecture                            │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────────┐ │
│  │                          Frontend Layer                                 │ │
│  │                                                                         │ │
│  │  • Static File Caching            • CDN Integration                     │ │
│  │  • Gzip Compression               • Browser Caching                     │ │
│  │  • Image Optimization             • Minification                        │ │
│  │  • Lazy Loading                   • Critical CSS                        │ │
│  └─────────────────────────────────────────────────────────────────────────┘ │
│                                      │                                       │
│  ┌─────────────────────────────────────────────────────────────────────────┐ │
│  │                        Application Layer                                │ │
│  │                                                                         │ │
│  │  • Query Optimization             • Connection Pooling                  │ │
│  │  • Cache-First Strategy           • Async Processing                    │ │
│  │  • Database Indexing              • Session Optimization               │ │
│  │  • N+1 Query Prevention           • Memory Management                   │ │
│  └─────────────────────────────────────────────────────────────────────────┘ │
│                                      │                                       │
│  ┌─────────────────────────────────────────────────────────────────────────┐ │
│  │                         Database Layer                                  │ │
│  │                                                                         │ │
│  │  • Read Replicas                  • Query Plan Optimization             │ │
│  │  • Partitioning                   • Vacuum & Analyze                    │ │
│  │  • Connection Pooling             • Materialized Views                  │ │
│  │  • Index Optimization             • Archive Strategy                    │ │
│  └─────────────────────────────────────────────────────────────────────────┘ │
│                                      │                                       │
│  ┌─────────────────────────────────────────────────────────────────────────┐ │
│  │                       Infrastructure Layer                              │ │
│  │                                                                         │ │
│  │  • Horizontal Scaling             • Load Balancing                      │ │
│  │  • Auto-scaling                   • Resource Monitoring                 │ │
│  │  • Geographic Distribution        • Performance Tuning                  │ │
│  │  • Container Optimization         • Network Optimization               │ │
│  └─────────────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Monitoring & Observability

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                       Monitoring & Observability                           │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────────┐ │
│  │                           Metrics Layer                                 │ │
│  │                                                                         │ │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────────┐ │ │
│  │  │ Application │  │  Database   │  │    Cache    │  │   Infrastructure│ │ │
│  │  │   Metrics   │  │   Metrics   │  │   Metrics   │  │     Metrics     │ │ │
│  │  │(Request/sec)│  │(Query Time) │  │(Hit/Miss)   │  │  (CPU/Memory)   │ │ │
│  │  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────────┘ │ │
│  └─────────────────────────────────────────────────────────────────────────┘ │
│                                      │                                       │
│  ┌─────────────────────────────────────────────────────────────────────────┐ │
│  │                           Logging Layer                                 │ │
│  │                                                                         │ │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────────┐ │ │
│  │  │Application  │  │   Access    │  │   Error     │  │    Audit        │ │ │
│  │  │    Logs     │  │    Logs     │  │    Logs     │  │     Logs        │ │ │
│  │  │  (Structured│  │   (Nginx)   │  │ (Exceptions)│  │  (Activities)   │ │ │
│  │  │    JSON)    │  │             │  │             │  │                 │ │ │
│  │  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────────┘ │ │
│  └─────────────────────────────────────────────────────────────────────────┘ │
│                                      │                                       │
│  ┌─────────────────────────────────────────────────────────────────────────┐ │
│  │                          Tracing Layer                                  │ │
│  │                                                                         │ │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────────┐ │ │
│  │  │  Request    │  │   Database  │  │    Cache    │  │    External     │ │ │
│  │  │  Tracing    │  │   Queries   │  │  Operations │  │   API Calls     │ │ │
│  │  │             │  │             │  │             │  │                 │ │ │
│  │  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────────┘ │ │
│  └─────────────────────────────────────────────────────────────────────────┘ │
│                                      │                                       │
│  ┌─────────────────────────────────────────────────────────────────────────┐ │
│  │                         Alerting Layer                                  │ │
│  │                                                                         │ │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────────┐ │ │
│  │  │   Uptime    │  │ Performance │  │   Error     │  │    Security     │ │ │
│  │  │   Alerts    │  │   Alerts    │  │   Alerts    │  │    Alerts       │ │ │
│  │  │             │  │             │  │             │  │                 │ │ │
│  │  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────────┘ │ │
│  └─────────────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

This architecture documentation provides a comprehensive overview of the system design, from high-level components to detailed implementation specifics. Each layer is designed for scalability, security, and maintainability while supporting the requirements for a modern web application.   - Redis for session data
   - File system for downloaded geographic data
   - TTL-based cache invalidation

3. **Rate Limiting**
   - Token bucket algorithm
   - 100 calls/minute default (configurable)
   - Thread-safe implementation
   - Graceful backoff on limit exceeded

4. **Database Optimization**
   - Connection pooling
   - Prepared statements
   - Index optimization for queries
   - Batch inserts for bulk operations

### Performance Metrics

| Operation | Target | Actual |
|-----------|--------|--------|
| Import 100k countries | <5 min | TBD |
| Sync 10k cities | <2 min | TBD |
| API call latency | <100ms | TBD |
| Memory usage (100k records) | <512MB | TBD |

## Security Model

### Authentication & Authorization

```
┌─────────────────────────────────────┐
│     NetBox API Token                │
│  (Stored in Environment Variables)  │
└─────────────────────────────────────┘
              │
              ▼
┌─────────────────────────────────────┐
│   NetBox Client (HTTPS Only)        │
│   • SSL Verification (Default: On)  │
│   • Token-based Authentication      │
│   • Request Signing                 │
└─────────────────────────────────────┘
```

### Security Features

1. **Credential Management**
   - No credentials in code
   - Environment variables or .env file
   - Pydantic validation of secrets
   - Optional HashiCorp Vault integration

2. **Network Security**
   - HTTPS only for NetBox API
   - SSL certificate verification
   - Configurable timeouts
   - Rate limiting to prevent abuse

3. **Input Validation**
   - Pydantic models for all external data
   - Type safety with Python 3.13 type hints
   - Sanitization of user inputs
   - Schema validation for API responses

4. **Audit Logging**
   - Structured logging with Loguru
   - Request/response logging
   - Error tracking with context
   - Performance metrics

### Security Scanning

- **Bandit**: Static analysis for Python security issues
- **Safety**: Dependency vulnerability scanning
- **CodeQL**: Advanced code analysis
- **Trivy**: Container image scanning

## Deployment Architecture

### Docker Deployment

```
┌──────────────────────────────────────────────────┐
│           Docker Host                             │
│                                                   │
│  ┌─────────────────────────────────────────────┐ │
│  │  netbox-geo-app Container                   │ │
│  │  • Python 3.13.1                            │ │
│  │  • Non-root user (appuser)                  │ │
│  │  • Volume: ./src → /app/src                 │ │
│  │  • Volume: ./cache → /app/cache             │ │
│  └─────────────────────────────────────────────┘ │
│                      │                            │
│  ┌──────────────────┼──────────────────────────┐ │
│  │                  ▼                           │ │
│  │  ┌───────────────────┐  ┌─────────────────┐ │ │
│  │  │   PostgreSQL 17   │  │   Redis 7       │ │ │
│  │  │   (Metadata DB)   │  │   (Session)     │ │ │
│  │  └───────────────────┘  └─────────────────┘ │ │
│  └─────────────────────────────────────────────┘ │
│                                                   │
│  Network: netbox-geo-network (bridge)            │
└──────────────────────────────────────────────────┘
```

### Production Deployment

```
┌────────────────────────────────────────────────────┐
│              Production Environment                 │
│                                                     │
│  ┌────────────────────────────────────────────────┐│
│  │  Load Balancer (nginx/HAProxy)                 ││
│  └────────────────────────────────────────────────┘│
│                      │                              │
│       ┌──────────────┼──────────────┐               │
│       ▼              ▼              ▼               │
│  ┌─────────┐   ┌─────────┐   ┌─────────┐           │
│  │ App 1   │   │ App 2   │   │ App 3   │           │
│  │ (Docker)│   │ (Docker)│   │ (Docker)│           │
│  └─────────┘   └─────────┘   └─────────┘           │
│       │              │              │               │
│       └──────────────┼──────────────┘               │
│                      ▼                              │
│  ┌────────────────────────────────────────────────┐│
│  │  PostgreSQL Cluster (Primary + Replicas)       ││
│  └────────────────────────────────────────────────┘│
│                      │                              │
│                      ▼                              │
│  ┌────────────────────────────────────────────────┐│
│  │  Redis Cluster (Master + Slaves)               ││
│  └────────────────────────────────────────────────┘│
└────────────────────────────────────────────────────┘
```

### Scalability

- **Horizontal Scaling**: Multiple application instances behind load balancer
- **Vertical Scaling**: Increase resources per container
- **Database Scaling**: PostgreSQL replication, Redis clustering
- **Caching**: Multi-tier caching strategy

## Technology Stack

### Core Technologies

| Component | Technology | Version | Purpose |
|-----------|-----------|---------|---------|
| Language | Python | 3.13.1 | Application runtime |
| NetBox Client | pynetbox | 7.5.0 | NetBox API integration |
| Configuration | Pydantic | 2.10.3 | Settings & validation |
| CLI Framework | Click | 8.1.8 | Command-line interface |
| Terminal UI | Rich | 13.9.4 | Beautiful terminal output |
| Logging | Loguru | 0.7.3 | Structured logging |
| Geo Processing | GeoPandas | 1.0.1 | Geographic data |
| HTTP Client | requests | 2.32.3 | HTTP requests |
| Database ORM | SQLAlchemy | 2.0.36 | Database abstraction |
| Migration | Alembic | 1.14.0 | Schema migrations |

### Development Tools

| Tool | Version | Purpose |
|------|---------|---------|
| Black | 24.10.0 | Code formatting |
| Flake8 | 7.1.1 | Code linting |
| isort | 5.13.2 | Import sorting |
| MyPy | 1.13.0 | Static type checking |
| pytest | 8.3.4 | Testing framework |
| Bandit | 1.7.10 | Security scanning |
| Safety | 3.2.11 | Dependency scanning |

## Future Enhancements

### Planned Features

1. **Additional Data Sources**
   - MaxMind GeoIP2
   - IP2Location
   - Custom CSV/JSON imports

2. **Enhanced APIs**
   - REST API for programmatic access
   - GraphQL endpoint
   - Webhook support

3. **UI Development**
   - Web dashboard
   - Interactive maps
   - Data visualization

4. **Advanced Features**
   - Incremental updates
   - Change detection
   - Conflict resolution
   - Data quality scoring

### Performance Improvements

- Async/await for I/O operations
- Parallel processing with multiprocessing
- Advanced caching strategies
- Query optimization

## Monitoring & Observability

### Logging Strategy

```python
# Structured logging with context
logger.info(
    "Importing countries",
    source="geonames",
    batch_size=1000,
    total_records=195
)
```

### Metrics Collection

- Request/response times
- Error rates
- Cache hit/miss ratios
- API rate limit consumption
- Import success/failure rates

### Health Checks

- Database connectivity
- Redis availability
- NetBox API reachability
- Disk space for cache
- Memory usage

## Conclusion

The NetBox Geo FOSS architecture is designed for:

- **Reliability**: Comprehensive error handling, retries, validation
- **Performance**: Bulk operations, caching, rate limiting
- **Maintainability**: Clear separation of concerns, type safety, documentation
- **Security**: Input validation, credential management, audit logging
- **Scalability**: Horizontal scaling, distributed caching, async operations

For questions or contributions, see [CONTRIBUTING.md](CONTRIBUTING.md).
