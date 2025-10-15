# Quick Start Guide

Get your private WinGet repository running in 5 minutes!

## Prerequisites

- Docker 20.10+
- Docker Compose 2.0+
- SSL certificates (or generate self-signed for testing)

## Step-by-Step Setup

### 1. Clone and Configure

```bash
cd winget-repo/deploy
cp .env.example .env
```

### 2. Edit Environment Variables

**Minimal required changes in `.env`:**

```bash
# Generate a secure JWT secret (64+ characters)
JWT_SECRET=$(openssl rand -hex 32)

# Set secure passwords
POSTGRES_PASSWORD=$(openssl rand -base64 32)
S3_ACCESS_KEY=$(openssl rand -hex 16)
S3_SECRET_KEY=$(openssl rand -hex 32)
SERVICE_PASSWORD=$(openssl rand -base64 24)

# Set your domain
BASE_URL=https://repo.example.com
DOMAIN=repo.example.com
```

**On Linux/Mac:**
```bash
# Auto-generate secrets
sed -i "s/JWT_SECRET=.*/JWT_SECRET=$(openssl rand -hex 32)/" .env
sed -i "s/POSTGRES_PASSWORD=.*/POSTGRES_PASSWORD=$(openssl rand -base64 32)/" .env
sed -i "s/S3_ACCESS_KEY=.*/S3_ACCESS_KEY=$(openssl rand -hex 16)/" .env
sed -i "s/S3_SECRET_KEY=.*/S3_SECRET_KEY=$(openssl rand -hex 32)/" .env
sed -i "s/SERVICE_PASSWORD=.*/SERVICE_PASSWORD=$(openssl rand -base64 24)/" .env
```

**On Windows PowerShell:**
```powershell
# Generate random passwords
$jwt = -join ((48..57) + (65..90) + (97..122) | Get-Random -Count 64 | % {[char]$_})
(Get-Content .env) -replace 'JWT_SECRET=.*', "JWT_SECRET=$jwt" | Set-Content .env
```

### 3. Add SSL Certificates

**Option A: Use existing certificates**

```bash
cp /path/to/fullchain.pem deploy/certs/
cp /path/to/privkey.pem deploy/certs/
```

**Option B: Generate self-signed (TESTING ONLY)**

```bash
mkdir -p deploy/certs
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout deploy/certs/privkey.pem \
  -out deploy/certs/fullchain.pem \
  -subj "/CN=repo.example.com"
```

### 4. Start Services

```bash
cd deploy
docker compose up -d --build
```

**Wait for services to initialize (2-3 minutes):**

```bash
# Watch logs
docker compose logs -f

# Wait for "Application started successfully"
```

### 5. Create Admin User

```bash
docker compose exec backend python create_admin.py
```

**Use defaults or enter custom:**
- Username: `admin`
- Email: `admin@example.com`
- Password: `admin123` (CHANGE THIS!)

### 6. Create Service Account

```bash
docker compose exec backend python -c "
import asyncio
from app.models import User, UserRole
from app.security import hash_password
from app.database import AsyncSessionLocal

async def create_service():
    async with AsyncSessionLocal() as session:
        # Get password from env
        import os
        password = os.getenv('SERVICE_PASSWORD', 'changeme')

        user = User(
            username='service',
            email='service@internal',
            password_hash=hash_password(password),
            role=UserRole.SERVICE,
            is_active=True
        )
        session.add(user)
        await session.commit()
        print('Service user created successfully')

asyncio.run(create_service())
"
```

### 7. Verify Services

```bash
# Check all services are running
docker compose ps

# Expected output:
# NAME                    STATUS
# winget-repo-backend     Up (healthy)
# winget-repo-db          Up (healthy)
# winget-repo-minio       Up (healthy)
# winget-repo-nginx       Up
# winget-repo-updater     Up
```

**Test endpoints:**

```bash
# Health check
curl -k https://localhost/health

# WinGet information
curl -k https://localhost/information
```

### 8. Access Web UI

Open browser: `https://repo.example.com` (or `https://localhost`)

**Login:**
- Username: `admin`
- Password: `admin123`

**First steps in UI:**
1. Go to Dashboard - verify statistics
2. Go to Packages - should be empty initially
3. Check Settings - review allow-list

### 9. Configure Allow-List

Edit `updater/allow-list.json`:

```json
{
  "packages": [
    {
      "package_identifier": "7zip.7zip",
      "architectures": ["x64"],
      "installer_types": ["msi"],
      "max_versions": 2
    }
  ]
}
```

**Restart updater to apply:**

```bash
docker compose restart updater
```

**Monitor sync:**

```bash
docker compose logs -f updater
```

Wait 5-10 minutes for first sync to complete.

### 10. Test WinGet Client

**On Windows machine:**

```powershell
# Add repository source
winget source add -n Private -t Microsoft.Rest -a https://repo.example.com

# If using self-signed certificate, you'll need to import it first:
# Import-Certificate -FilePath "fullchain.pem" -CertStoreLocation Cert:\LocalMachine\Root

# Search packages
winget search 7zip --source Private

# Show package details
winget show 7zip.7zip --source Private

# Install package
winget install 7zip.7zip --source Private
```

## Troubleshooting

### Services won't start

```bash
# Check logs
docker compose logs backend
docker compose logs db

# Restart
docker compose restart
```

### Can't connect to UI

```bash
# Check nginx
docker compose logs nginx

# Verify certificates
ls -la deploy/certs/

# Test locally
curl -k https://localhost/health
```

### WinGet can't connect

```powershell
# Test connectivity
Test-NetConnection -ComputerName repo.example.com -Port 443

# Test HTTPS
Invoke-WebRequest -Uri https://repo.example.com/information

# Check WinGet sources
winget source list
```

### Updater not syncing

```bash
# Check logs
docker compose logs updater

# Verify service user exists
docker compose exec backend python -c "
import asyncio
from sqlalchemy import select
from app.models import User
from app.database import AsyncSessionLocal

async def check():
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(User).where(User.username == 'service'))
        user = result.scalar_one_or_none()
        if user:
            print(f'Service user found: {user.username} (role: {user.role.value})')
        else:
            print('Service user NOT FOUND - run create service script!')

asyncio.run(check())
"

# Manual trigger
docker compose restart updater
```

### Database issues

```bash
# Check database connection
docker compose exec db psql -U winget -d winget_repo -c "SELECT 1"

# Run migrations
docker compose exec backend alembic upgrade head

# Check migrations
docker compose exec backend alembic current
```

## Next Steps

✅ **Production Checklist:**

1. Change default admin password
2. Review security settings in `.env`
3. Set up SSL certificate auto-renewal
4. Configure backups (database + MinIO)
5. Set up monitoring (Prometheus/Grafana)
6. Review nginx rate limits
7. Test WinGet from multiple clients
8. Document recovery procedures

✅ **Optional Enhancements:**

- Add more packages to allow-list
- Configure external S3 (AWS/DigitalOcean)
- Set up CI/CD for updates
- Add Prometheus metrics endpoint
- Configure log aggregation (ELK)
- Set up alerts (email/Slack)

## Common Commands

```bash
# View logs
docker compose logs -f [service]

# Restart service
docker compose restart [service]

# Stop all
docker compose down

# Start all
docker compose up -d

# Rebuild after code changes
docker compose up -d --build

# Database backup
docker compose exec db pg_dump -U winget winget_repo > backup.sql

# Database restore
cat backup.sql | docker compose exec -T db psql -U winget winget_repo

# Check resource usage
docker stats
```

## Support

- **Full Documentation**: See [README.md](README.md)
- **Architecture Details**: See [DIRECTORY_STRUCTURE.md](DIRECTORY_STRUCTURE.md)
- **Issues**: Check logs first, then file GitHub issue

---

**Congratulations!** Your private WinGet repository is now running! 🎉
