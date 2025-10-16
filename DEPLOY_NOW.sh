#!/bin/bash
# =================================================================
# ФИНАЛЬНЫЙ ДЕПЛОЙ - ВСЁ ПРОТЕСТИРОВАНО ЛОКАЛЬНО И РАБОТАЕТ!
# =================================================================

set -e  # Exit on error

echo "================================================================"
echo "Deploying tested and working version to cofemon.online"
echo "================================================================"
echo ""

# 1. Pull latest changes
echo "Step 1/5: Pulling latest changes from GitHub..."
cd /root/winget-repo
git pull origin main
echo "✓ Latest commit:"
git log --oneline -1
echo ""

# 2. Rebuild backend with JWT fix
echo "Step 2/5: Rebuilding backend with JWT fix..."
cd deploy
docker compose up -d --build backend
echo "✓ Backend rebuild started"
echo ""

# 3. Wait for backend to start
echo "Step 3/5: Waiting for backend to start (20 seconds)..."
sleep 20
echo "✓ Backend should be ready"
echo ""

# 4. Test authentication
echo "Step 4/5: Testing authentication..."
docker compose exec -T backend python -c "
import requests
print('Testing login...')
resp = requests.post('http://localhost:8000/api/auth/login', json={'username':'admin','password':'admin123'}, timeout=5)
if resp.status_code == 200:
    token = resp.json()['access_token']
    print('✓ Login successful')
    me_resp = requests.get('http://localhost:8000/api/auth/me', headers={'Authorization': f'Bearer {token}'}, timeout=5)
    if me_resp.status_code == 200:
        print('✓ /auth/me successful:', me_resp.json()['username'])
        print('✓✓✓ AUTHENTICATION WORKING!')
    else:
        print('✗ /auth/me failed:', me_resp.status_code)
        exit(1)
else:
    print('✗ Login failed:', resp.status_code)
    exit(1)
" || {
    echo "✗ Test failed - checking backend logs..."
    docker compose logs --tail=50 backend
    exit 1
}
echo ""

# 5. Rebuild frontend
echo "Step 5/5: Rebuilding frontend..."
docker compose down frontend-builder nginx
docker compose up -d --build frontend-builder
sleep 10
docker compose up -d nginx
echo "✓ Frontend and nginx restarted"
echo ""

# Final status
echo "================================================================"
echo "DEPLOYMENT COMPLETE!"
echo "================================================================"
docker compose ps
echo ""
echo "Test the site: https://cofemon.online/login"
echo "Credentials: admin / admin123"
echo "================================================================"
