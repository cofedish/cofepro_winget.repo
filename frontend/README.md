# Frontend - WinGet Repository

React + Vite + Tailwind CSS + shadcn/ui frontend for Private WinGet Repository.

## Quick Start

### Docker (Recommended)

The frontend is built automatically as part of the docker-compose stack:

```bash
cd ../deploy
docker compose up --build frontend-builder
```

### Local Development

```bash
# Install dependencies
npm install

# Generate package-lock.json (if missing)
npm install --package-lock-only

# Start dev server
npm run dev

# Build for production
npm run build
```

## Package Lock File

The Dockerfile supports both scenarios:
- **With `package-lock.json`**: Uses `npm ci` (faster, deterministic)
- **Without `package-lock.json`**: Falls back to `npm install`

### Generate package-lock.json

```bash
# Option 1: Using script
chmod +x generate-lockfile.sh
./generate-lockfile.sh

# Option 2: Manual
npm install --package-lock-only
```

## Build Output

The build output goes to `/app/dist` inside the container, which is then copied to the shared volume `/out` that nginx serves.

## Environment

No environment variables needed - all API calls go through nginx proxy.

## Technologies

- React 18
- TypeScript
- Vite 5
- Tailwind CSS 3
- shadcn/ui components
- TanStack Query (React Query)
- React Router 6
- Axios
