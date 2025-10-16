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
# Test login
LOGIN_RESP=$(docker compose exec -T backend curl -s -w "\n%{http_code}" \
    -X POST http://localhost:8000/api/auth/login \
    -H "Content-Type: application/json" \
    -d '{"username":"admin","password":"admin123"}')

LOGIN_CODE=$(echo "$LOGIN_RESP" | tail -n1)
LOGIN_BODY=$(echo "$LOGIN_RESP" | head -n-1)

if [ "$LOGIN_CODE" = "200" ]; then
    echo "✓ Login successful"
    TOKEN=$(echo "$LOGIN_BODY" | grep -o '"access_token":"[^"]*"' | cut -d'"' -f4)

    # Test /auth/me
    ME_RESP=$(docker compose exec -T backend curl -s -w "\n%{http_code}" \
        http://localhost:8000/api/auth/me \
        -H "Authorization: Bearer $TOKEN")

    ME_CODE=$(echo "$ME_RESP" | tail -n1)
    ME_BODY=$(echo "$ME_RESP" | head -n-1)

    if [ "$ME_CODE" = "200" ]; then
        USERNAME=$(echo "$ME_BODY" | grep -o '"username":"[^"]*"' | cut -d'"' -f4)
        echo "✓ /auth/me successful: $USERNAME"
        echo "✓✓✓ AUTHENTICATION WORKING!"
    else
        echo "✗ /auth/me failed: $ME_CODE"
        echo "$ME_BODY"
        docker compose logs --tail=50 backend
        exit 1
    fi
else
    echo "✗ Login failed: $LOGIN_CODE"
    echo "$LOGIN_BODY"
    docker compose logs --tail=50 backend
    exit 1
fi
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
