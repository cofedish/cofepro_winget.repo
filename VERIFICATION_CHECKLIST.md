# Проверочный чек-лист после применения фиксов

## ✅ Все исправления применены

### Изменено файлов: 14

1. ✅ `backend/app/models.py` - metadata → meta
2. ✅ `backend/app/schemas.py` - Pydantic v2 алиасы
3. ✅ `backend/app/utils.py` - параметр meta
4. ✅ `backend/app/routers/admin.py` - вызовы meta (8 мест)
5. ✅ `backend/app/routers/upload.py` - вызовы meta (2 места)
6. ✅ `backend/app/main.py` - healthcheck "ok"
7. ✅ `deploy/docker-compose.yml` - frontend /out, version удалён
8. ✅ `deploy/nginx.conf` - events, http, proxy_max_temp_file_size
9. ✅ `backend/Dockerfile` - оптимизация
10. ✅ `frontend/Dockerfile` - условный npm ci/install

### Создано новых файлов: 4

11. ✅ `frontend/package-lock.json` - минимальный lockfile
12. ✅ `frontend/generate-lockfile.sh` - скрипт генерации
13. ✅ `frontend/README.md` - инструкции
14. ✅ `FIXES_APPLIED.md` - документация исправлений

---

## 🚀 Команды для запуска

```bash
# 1. Перейти в директорию deploy
cd E:\Projects\S7\winget-repo\deploy

# 2. Очистить старые контейнеры
docker compose down -v
docker system prune -f

# 3. Убедиться что .env настроен
# Проверить что JWT_SECRET, пароли и т.д. заданы
cat .env

# 4. Запустить всё
docker compose up -d --build

# 5. Следить за логами
docker compose logs -f
```

---

## 🔍 Проверки (выполнить по порядку)

### 1. Backend запустился

```bash
docker compose logs backend | tail -20
```

**Ожидается:**
```
✅ Running database migrations...
✅ INFO  [alembic.runtime.migration] Running upgrade  -> 001
✅ Starting backend server...
✅ Application started successfully
```

**НЕ должно быть:**
```
❌ InvalidRequestError: Attribute name 'metadata' is reserved
❌ sqlalchemy.exc
```

---

### 2. Frontend собрался

```bash
docker compose logs frontend-builder
```

**Ожидается:**
```
✅ npm ci (или npm install)
✅ vite build
✅ Frontend build complete
```

**НЕ должно быть:**
```
❌ npm error code EUSAGE
❌ cp: 'dist/assets' and '/app/dist/assets' are the same file
```

---

### 3. Nginx валидный

```bash
docker compose exec nginx nginx -t
```

**Ожидается:**
```
✅ nginx: configuration file /etc/nginx/nginx.conf test is successful
```

---

### 4. Healthcheck работает

```bash
curl -sSf http://localhost/health
```

**Ожидается:**
```json
{"status":"ok","version":"1.0.0","environment":"production"}
```

---

### 5. WinGet API работает

```bash
curl -sSf http://localhost/information
```

**Ожидается:**
```json
{
  "Data": {
    "SourceIdentifier": "Private.WinGet.Source",
    "ServerSupportedVersions": ["1.0.0", ..., "1.7.0"]
  }
}
```

---

### 6. Frontend статика отдаётся

```bash
curl -I http://localhost/
```

**Ожидается:**
```
✅ HTTP/1.1 200 OK
✅ Server: nginx
```

---

### 7. Все сервисы здоровы

```bash
docker compose ps
```

**Ожидается:**
```
NAME                        STATUS
winget-repo-backend         Up (healthy)
winget-repo-db              Up (healthy)
winget-repo-minio           Up (healthy)
winget-repo-nginx           Up
winget-repo-updater         Up
```

---

### 8. Создать админа

```bash
docker compose exec backend python create_admin.py
```

**Ввести данные или использовать defaults:**
- Username: `admin`
- Email: `admin@example.com`
- Password: `admin123` (СМЕНИТЬ В PRODUCTION!)

**Ожидается:**
```
✅ Admin user created successfully!
```

---

### 9. Создать service аккаунт

```bash
docker compose exec backend python -c "
import asyncio
import os
from app.models import User, UserRole
from app.security import hash_password
from app.database import AsyncSessionLocal

async def create_service():
    async with AsyncSessionLocal() as session:
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

**Ожидается:**
```
✅ Service user created successfully
```

---

### 10. Проверить логин в UI

```bash
# Открыть в браузере
http://localhost/

# Залогиниться
Username: admin
Password: admin123
```

**Ожидается:**
- ✅ Страница логина загружается
- ✅ После логина попадаем на Dashboard
- ✅ Видим статистику (0 packages, 0 versions, и т.д.)

---

### 11. Проверить audit logs API

```bash
# Получить токен
TOKEN=$(curl -s -X POST http://localhost/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}' | jq -r '.access_token')

# Проверить что токен получен
echo $TOKEN

# Запросить audit logs
curl -s http://localhost/api/admin/audit-logs \
  -H "Authorization: Bearer $TOKEN" | jq '.'
```

**Ожидается:**
```json
[
  {
    "id": 1,
    "actor_username": "system",
    "action": "create",
    "entity_type": "user",
    "metadata": {...},  // ✅ Поле называется "metadata" в JSON
    ...
  }
]
```

---

## 🎯 Acceptance Criteria (финальная проверка)

- [ ] 1. Backend стартует без ошибок `metadata reserved`
- [ ] 2. Миграции Alembic проходят успешно
- [ ] 3. `/health` возвращает `200` с `status: "ok"`
- [ ] 4. Frontend builder собирается без ошибки `same file`
- [ ] 5. Nginx конфигурация валидна (`nginx -t`)
- [ ] 6. WinGet API `/information` возвращает `200`
- [ ] 7. Frontend статика отдаётся nginx
- [ ] 8. Audit logs API возвращает `metadata` в JSON
- [ ] 9. Все healthchecks проходят
- [ ] 10. UI логин работает
- [ ] 11. Dashboard показывает статистику

---

## 🐛 Troubleshooting

### Backend не стартует

```bash
# Проверить логи
docker compose logs backend -f

# Проверить БД
docker compose exec db psql -U winget -d winget_repo -c "SELECT 1"

# Пересобрать
docker compose up -d --build backend
```

### Frontend не собирается

```bash
# Проверить логи
docker compose logs frontend-builder

# Если ошибка с package-lock.json:
# Удалить его и пересобрать (Dockerfile поддерживает npm install)
rm ../frontend/package-lock.json
docker compose up -d --build frontend-builder
```

### Nginx не стартует

```bash
# Проверить конфигурацию
docker compose exec nginx nginx -t

# Проверить логи
docker compose logs nginx

# Проверить что порты не заняты
netstat -an | grep :80
netstat -an | grep :443
```

### Updater падает

```bash
# Проверить что service аккаунт создан
docker compose exec backend python -c "
from app.models import User
from app.database import AsyncSessionLocal
from sqlalchemy import select
import asyncio

async def check():
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(User).where(User.username == 'service'))
        user = result.scalar_one_or_none()
        print(f'Service user: {user.username if user else \"NOT FOUND\"}')

asyncio.run(check())
"

# Проверить allow-list.json
cat ../updater/allow-list.json

# Проверить логи
docker compose logs updater -f
```

---

## 📋 Что дальше

После успешной проверки всех пунктов:

1. ✅ Изменить дефолтный пароль админа
2. ✅ Настроить SSL сертификаты (`deploy/certs/`)
3. ✅ Обновить `BASE_URL` и `DOMAIN` в `.env`
4. ✅ Настроить `updater/allow-list.json` (добавить нужные пакеты)
5. ✅ Опционально: Сгенерировать полный `package-lock.json`
6. ✅ Настроить бэкапы (см. README.md)
7. ✅ Настроить мониторинг
8. ✅ Протестировать с Windows клиентом:

```powershell
# На Windows машине
winget source add -n Private -t Microsoft.Rest -a https://<DOMAIN>
winget search 7zip --source Private
```

---

**Все исправления применены и готовы к проверке! 🎉**
