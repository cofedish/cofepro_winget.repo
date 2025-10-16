#!/bin/bash
# ================================================================
# ФИНАЛЬНОЕ ИСПРАВЛЕНИЕ: Команды для выполнения на сервере
# ================================================================

echo "================================================================"
echo "Fixing login issue on cofemon.online"
echo "================================================================"
echo ""

# Переход в директорию проекта
cd /root/winget-repo || exit 1
echo "✓ Changed to project directory"

# Получение последних изменений
echo ""
echo "--- Pulling latest changes from GitHub ---"
git pull origin main
echo "✓ Git pull completed"

# Показать последний коммит
echo ""
echo "--- Latest commit ---"
git log --oneline -1

# Пересборка backend
echo ""
echo "--- Rebuilding backend with fixes ---"
cd deploy || exit 1
docker compose up -d --build backend
echo "✓ Backend rebuild started"

# Пересборка frontend
echo ""
echo "--- Rebuilding frontend with logging ---"
docker compose down frontend-builder nginx
docker compose up -d --build frontend-builder
echo "✓ Frontend rebuild started"

# Ожидание запуска backend
echo ""
echo "--- Waiting for backend to start (20 seconds) ---"
sleep 20

# Запуск nginx
echo ""
echo "--- Starting nginx ---"
docker compose up -d nginx
echo "✓ Nginx started"

# Проверка статуса сервисов
echo ""
echo "--- Checking services status ---"
docker compose ps

# Тестирование аутентификации
echo ""
echo "--- Testing authentication ---"
docker compose exec -T backend python test_auth.py

echo ""
echo "================================================================"
echo "DEPLOYMENT COMPLETE!"
echo "================================================================"
echo ""
echo "Now try to login at: https://cofemon.online/login"
echo "Username: admin"
echo "Password: admin123"
echo ""
echo "Check browser console for [AUTH] logs"
echo "================================================================"
