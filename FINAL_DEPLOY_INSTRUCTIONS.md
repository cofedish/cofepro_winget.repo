# 🚀 ФИНАЛЬНЫЕ ИНСТРУКЦИИ ПО ДЕПЛОЮ

## Проблема
1. Backend не может валидировать JWT токены → 401 на `/auth/me`
2. Frontend не собирался из-за отсутствия `api.ts` в git

## Решение
Все исправления уже в GitHub. Нужно только применить их на сервере.

---

## 📋 КОМАНДЫ ДЛЯ ВЫПОЛНЕНИЯ НА СЕРВЕРЕ

### Вариант 1: Автоматический (рекомендуется)

```bash
ssh root@cofemon.online
# Пароль: GLtr7BsrQ053

cd /root/winget-repo
git pull origin main
chmod +x FINAL_FIX_COMMANDS.sh
./FINAL_FIX_COMMANDS.sh
```

### Вариант 2: Пошаговый (если автоматический не работает)

```bash
ssh root@cofemon.online
# Пароль: GLtr7BsrQ053

# 1. Получить последние изменения
cd /root/winget-repo
git pull origin main

# 2. Проверить что файлы на месте
ls frontend/src/lib/
# Должны быть: api.ts, auth.tsx, cn.ts

# 3. Перейти в директорию deploy
cd deploy

# 4. Пересобрать backend
echo "Rebuilding backend..."
docker compose up -d --build backend

# 5. Пересобрать frontend
echo "Rebuilding frontend..."
docker compose down frontend-builder nginx
docker compose up -d --build frontend-builder

# 6. Подождать 30 секунд
echo "Waiting for services to start..."
sleep 30

# 7. Запустить nginx
echo "Starting nginx..."
docker compose up -d nginx

# 8. Проверить статус
echo "Checking services..."
docker compose ps

# 9. Тестировать аутентификацию
echo "Testing authentication..."
docker compose exec -T backend python test_auth.py
```

---

## ✅ Проверка результата

### 1. Проверьте что backend видит исправление:

```bash
cd /root/winget-repo/deploy
docker compose exec backend python -c "
import inspect
from app.security import create_tokens_for_user
source = inspect.getsource(create_tokens_for_user)
if 'hasattr' in source:
    print('✓ Backend has the fix!')
else:
    print('✗ Backend NOT updated - rebuild needed')
"
```

### 2. Проверьте что frontend собрался:

```bash
docker compose logs frontend-builder | grep -E "build|error|Build"
# Должно быть: "dist/index.html" и без ошибок
```

### 3. Проверьте логин через curl:

```bash
# Login
TOKEN=$(curl -s -X POST https://cofemon.online/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}' | \
  grep -o '"access_token":"[^"]*"' | cut -d'"' -f4)

# Get user info
curl -s https://cofemon.online/api/auth/me \
  -H "Authorization: Bearer $TOKEN"

# Должен вернуться JSON с данными пользователя:
# {"id":1,"username":"admin","email":"admin@example.com","role":"admin",...}
```

### 4. Проверьте в браузере:

1. Откройте https://cofemon.online/login
2. Откройте консоль браузера (F12)
3. Войдите (admin / admin123)
4. В консоли должны быть логи:
   ```
   [AUTH] Logging in... admin
   [AUTH] Login successful, received tokens
   [AUTH] Tokens saved to localStorage
   [AUTH] Fetching user info...
   [AUTH] User info received: {id: 1, username: "admin", ...}
   ```
5. Вас должно перенаправить на главную страницу

---

## 🔧 Если всё равно не работает

### Проблема: Backend возвращает 401 на /auth/me

**Решение:**
```bash
# Проверьте что backend пересобрался
cd /root/winget-repo/deploy
docker compose images backend
# Проверьте Created - должна быть свежая дата

# Если дата старая - пересоберите принудительно
docker compose build --no-cache backend
docker compose up -d backend
sleep 20
```

### Проблема: Frontend не собирается

**Решение:**
```bash
# Проверьте что файлы на месте
cd /root/winget-repo
ls -la frontend/src/lib/
# Должны быть: api.ts, auth.tsx, cn.ts

# Если файлов нет - проверьте git
git status
git log --oneline -1
# Должен быть коммит: ec07413 Исправлена проблема со сборкой frontend

# Пересоберите frontend
cd deploy
docker compose build --no-cache frontend-builder
docker compose up -d frontend-builder
```

---

## 📊 Ожидаемый результат

После выполнения всех команд:

- ✅ Backend запущен и здоров
- ✅ Frontend собран и работает
- ✅ Nginx проксирует запросы
- ✅ Логин через curl возвращает данные пользователя
- ✅ Логин через веб-интерфейс работает
- ✅ После логина открывается главная страница

---

## 🆘 Помощь

Если что-то не работает, выполните:

```bash
cd /root/winget-repo
python3 test_remote_auth.py
```

И покажите вывод. Это покажет на каком этапе происходит ошибка.
