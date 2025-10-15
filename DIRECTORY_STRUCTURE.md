# Project Directory Structure

```
winget-repo/
│
├── README.md                          # Main documentation
├── DIRECTORY_STRUCTURE.md             # This file
├── .gitignore                         # Git ignore rules
│
├── backend/                           # FastAPI Backend
│   ├── Dockerfile                     # Backend container image
│   ├── .dockerignore                  # Docker ignore rules
│   ├── requirements.txt               # Python dependencies
│   ├── alembic.ini                    # Alembic configuration
│   ├── create_admin.py                # Admin user creation script
│   │
│   ├── app/                           # Application code
│   │   ├── __init__.py
│   │   ├── main.py                    # FastAPI application entry point
│   │   ├── config.py                  # Settings and configuration
│   │   ├── database.py                # Database connection and session
│   │   ├── models.py                  # SQLAlchemy ORM models
│   │   ├── schemas.py                 # Pydantic schemas for validation
│   │   ├── security.py                # JWT auth and password hashing
│   │   ├── s3.py                      # S3/MinIO client
│   │   ├── utils.py                   # Utility functions
│   │   │
│   │   └── routers/                   # API route handlers
│   │       ├── __init__.py
│   │       ├── auth.py                # Authentication endpoints
│   │       ├── winget.py              # WinGet REST API endpoints
│   │       ├── admin.py               # Admin API endpoints
│   │       └── upload.py              # File upload/download endpoints
│   │
│   └── alembic/                       # Database migrations
│       ├── env.py                     # Alembic environment
│       ├── script.py.mako             # Migration template
│       └── versions/                  # Migration files
│           └── 001_initial_migration.py
│
├── frontend/                          # React Frontend
│   ├── Dockerfile                     # Frontend build container
│   ├── .dockerignore                  # Docker ignore rules
│   ├── package.json                   # Node dependencies
│   ├── tsconfig.json                  # TypeScript configuration
│   ├── tsconfig.node.json             # TypeScript Node configuration
│   ├── vite.config.ts                 # Vite build configuration
│   ├── tailwind.config.js             # Tailwind CSS configuration
│   ├── postcss.config.js              # PostCSS configuration
│   ├── index.html                     # HTML entry point
│   │
│   └── src/                           # Source code
│       ├── main.tsx                   # React entry point
│       ├── App.tsx                    # Main application component
│       ├── index.css                  # Global styles
│       ├── vite-env.d.ts              # Vite type definitions
│       │
│       ├── lib/                       # Utilities and libraries
│       │   ├── api.ts                 # Axios API client
│       │   ├── auth.tsx               # Authentication context
│       │   └── cn.ts                  # Class name utility
│       │
│       ├── components/                # React components
│       │   └── Layout.tsx             # Main layout component
│       │
│       └── pages/                     # Page components
│           ├── LoginPage.tsx          # Login page
│           ├── DashboardPage.tsx      # Dashboard page
│           └── PackagesPage.tsx       # Packages list page
│
├── updater/                           # Auto-mirror Service
│   ├── Dockerfile                     # Updater container image
│   ├── .dockerignore                  # Docker ignore rules
│   ├── requirements.txt               # Python dependencies
│   ├── config.py                      # Updater configuration
│   ├── main.py                        # Main updater logic
│   ├── winget_source.py               # Public WinGet API interface
│   └── allow-list.json                # Package whitelist configuration
│
└── deploy/                            # Deployment Configuration
    ├── docker-compose.yml             # Docker Compose orchestration
    ├── nginx.conf                     # Nginx reverse proxy config
    ├── .env.example                   # Environment variables template
    │
    └── certs/                         # SSL certificates directory
        └── README.md                  # Certificate setup instructions

```

## Component Descriptions

### Backend (`/backend`)

**Purpose**: REST API server implementing WinGet REST Source specification

**Key Technologies**:
- FastAPI (async web framework)
- SQLAlchemy + AsyncPG (async ORM for PostgreSQL)
- Alembic (database migrations)
- Boto3 (S3/MinIO client)
- Python-JOSE (JWT handling)
- Pydantic (data validation)

**Responsibilities**:
- WinGet REST API endpoints (`/information`, `/manifestSearch`, etc.)
- Admin API for package management
- File upload/download with streaming
- JWT authentication and authorization
- Database operations
- S3/MinIO integration
- Audit logging

### Frontend (`/frontend`)

**Purpose**: Web-based admin interface

**Key Technologies**:
- React 18 (UI library)
- TypeScript (type safety)
- Vite (build tool)
- Tailwind CSS (styling)
- shadcn/ui (component library)
- React Router (routing)
- TanStack Query (data fetching)
- Axios (HTTP client)

**Responsibilities**:
- User authentication UI
- Dashboard with statistics
- Package browsing and search
- Manual package upload
- Allow-list management
- Audit log viewing
- User management (admin)

### Updater (`/updater`)

**Purpose**: Automated package mirroring service

**Key Technologies**:
- Python 3.11+
- HTTPX (async HTTP client)
- SQLAlchemy (database access)
- Boto3 (S3 uploads)

**Responsibilities**:
- Periodic sync from public WinGet
- Package discovery via allow-list
- Installer download with SHA-256 verification
- S3 upload
- Database record creation via API
- Error handling and logging

### Deploy (`/deploy`)

**Purpose**: Infrastructure and orchestration

**Components**:
- **docker-compose.yml**: Orchestrates all services
  - PostgreSQL (database)
  - MinIO (S3-compatible storage)
  - Backend (FastAPI)
  - Frontend (nginx-served static files)
  - Nginx (reverse proxy + TLS termination)
  - Updater (background service)

- **nginx.conf**: Production-ready configuration
  - HTTPS with TLS 1.2/1.3
  - Security headers (HSTS, CSP, etc.)
  - Rate limiting
  - Reverse proxy to backend
  - Static file serving for frontend
  - Large file upload support (4GB)

- **.env**: Environment variables
  - Application settings
  - Database credentials
  - S3 credentials
  - JWT secrets
  - Feature flags

## Data Flow

### Package Installation (WinGet Client)

```
WinGet Client
    │
    ├─> GET /information (verify source)
    │
    ├─> POST /manifestSearch (find package)
    │
    ├─> GET /packageManifests/{id} (get latest manifest)
    │
    └─> GET /dl/{s3-key} (download installer)
            │
            └─> Streams from S3/MinIO
```

### Auto-Mirroring Flow

```
Updater Service (periodic)
    │
    ├─> Read allow-list.json
    │
    ├─> Query public WinGet API
    │   └─> Get latest version + manifest
    │
    ├─> Download installer (with SHA-256 check)
    │
    ├─> Upload to S3/MinIO
    │
    └─> Create DB records via Admin API
        ├─> Create Package (if new)
        ├─> Create Version
        └─> Create Installer
```

### Manual Upload Flow

```
Admin User (Web UI)
    │
    ├─> Login (JWT auth)
    │
    ├─> Create Package + Version
    │
    └─> Upload Installer
        │
        ├─> POST /api/admin/upload (with file)
        │   │
        │   ├─> Calculate SHA-256
        │   ├─> Upload to S3
        │   └─> Create DB record
        │
        └─> Installer available via /dl/{s3-key}
```

## Port Usage

| Service | Internal Port | External Port | Protocol |
|---------|--------------|---------------|----------|
| Nginx | 80, 443 | 80, 443 | HTTP/HTTPS |
| Backend | 8000 | - | HTTP (internal) |
| PostgreSQL | 5432 | - | PostgreSQL |
| MinIO | 9000, 9001 | - | HTTP (S3 API, Console) |

## Volume Mounts

| Volume | Purpose | Persistence |
|--------|---------|-------------|
| `postgres_data` | Database files | Persistent |
| `minio_data` | Installer files | Persistent |
| `frontend_dist` | Built frontend | Ephemeral (rebuilt) |
| `deploy/certs` | SSL certificates | Bind mount |
| `updater/allow-list.json` | Package whitelist | Bind mount |

## Network Architecture

All services run on `winget-network` Docker bridge network:

- Services communicate via service names (e.g., `backend:8000`)
- Only nginx exposes ports to host
- Internal services are isolated from external access
- DNS resolution via Docker

## Security Layers

1. **Network**: Only ports 80/443 exposed
2. **TLS**: All traffic encrypted (TLS 1.2/1.3)
3. **Authentication**: JWT tokens required for admin API
4. **Authorization**: Role-based access control
5. **Rate Limiting**: Per-endpoint limits in nginx
6. **Input Validation**: Pydantic schemas on all inputs
7. **SQL Injection**: SQLAlchemy ORM (parameterized queries)
8. **XSS**: React auto-escapes output
9. **CSRF**: SameSite cookies + CORS restrictions
10. **Audit Trail**: All actions logged to database

## Scalability Considerations

**Horizontal Scaling**:
- Backend: Multiple replicas behind nginx load balancer
- Database: PostgreSQL streaming replication
- Storage: MinIO distributed mode or external S3

**Vertical Scaling**:
- Increase worker count in gunicorn
- Allocate more CPU/RAM to containers
- Use faster storage (NVMe SSD)

**Bottlenecks**:
- Database (indexing, query optimization)
- File uploads (use CDN for downloads)
- Updater sync (parallel downloads)

## Backup Strategy

**What to Backup**:
1. PostgreSQL database (`postgres_data` volume)
2. MinIO files (`minio_data` volume)
3. Configuration files (`.env`, `allow-list.json`)
4. SSL certificates (`deploy/certs/`)

**Backup Methods**:
```bash
# Database
docker compose exec db pg_dump -U winget winget_repo > backup.sql

# MinIO
docker compose exec minio mc mirror myminio/winget-installers /backup/minio
```

**Recovery**:
```bash
# Database
cat backup.sql | docker compose exec -T db psql -U winget winget_repo

# MinIO
docker compose exec minio mc mirror /backup/minio myminio/winget-installers
```

## Development Workflow

1. **Local Development**: Run services individually (see README Development section)
2. **Testing**: Docker Compose with test database
3. **Staging**: Docker Compose with production-like config
4. **Production**: Docker Compose with monitoring + backups

## Monitoring Recommendations

- **Health Checks**: Built into docker-compose.yml
- **Metrics**: Add Prometheus exporter to backend
- **Logs**: Centralized logging (ELK, Loki)
- **Alerts**: Monitor service health, disk space, error rates
- **Uptime**: External monitoring (UptimeRobot, Pingdom)

## Performance Tuning

**Backend**:
- Increase worker count (default: 4)
- Enable caching (Redis)
- Database connection pooling (default: 20)

**Database**:
- Add indexes on frequently queried fields
- Regular VACUUM and ANALYZE
- Tune `shared_buffers`, `work_mem`

**Nginx**:
- Enable gzip compression
- Increase worker connections
- Tune keepalive timeouts

**S3/MinIO**:
- Use CDN for popular downloads
- Enable object lifecycle policies
- Implement multi-part uploads for large files
