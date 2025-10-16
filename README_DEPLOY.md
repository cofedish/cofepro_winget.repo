# 🎉 Готово к деплою на сервер!

## ✅ Что было сделано

### Локальное тестирование
- ✅ Поднят полный стек локально (backend, frontend, db, minio, nginx)
- ✅ Создан admin пользователь
- ✅ Протестирован логин через API
- ✅ Протестирован /auth/me endpoint
- ✅ Протестирован веб-интерфейс - логин работает!

### Исправленные проблемы
1. **JWT токены**: Исправлена ошибка "Subject must be a string"
   - `user.id` теперь конвертируется в строку при создании токена
   - При декодировании парсится обратно в int

2. **Frontend файлы**: Добавлены недостающие файлы в git
   - `frontend/src/lib/api.ts`
   - `frontend/src/lib/cn.ts`
   - `frontend/src/lib/auth.tsx`

3. **Логирование**: Добавлены console.log для отладки в auth.tsx

### Коммиты
- Последний коммит: `8974f89` - Добавлен скрипт для финального деплоя
- Исправление JWT: `74d1aa4` - ИСПРАВЛЕНО: Проблема с JWT токенами

---

## 🚀 Деплой на сервер

### Автоматический деплой (Рекомендуется)

```bash
ssh root@cofemon.online
# Пароль: GLtr7BsrQ053

cd /root/winget-repo
git pull origin main
chmod +x DEPLOY_NOW.sh
./DEPLOY_NOW.sh
```

### Ручной деплой

```bash
ssh root@cofemon.online
# Пароль: GLtr7BsrQ053

cd /root/winget-repo
git pull origin main

cd deploy
docker compose up -d --build backend
sleep 20

# Тест
TOKEN=$(curl -s -X POST https://localhost/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}' | \
  grep -o '"access_token":"[^"]*"' | cut -d'"' -f4)

curl -s https://localhost/api/auth/me \
  -H "Authorization: Bearer $TOKEN"

# Должен вернуть JSON с данными пользователя

# Пересобрать frontend
docker compose down frontend-builder nginx
docker compose up -d --build frontend-builder
sleep 10
docker compose up -d nginx
```

---

## ✅ Проверка после деплоя

### 1. API тест
```bash
# На сервере
cd /root/winget-repo/deploy
TOKEN=$(curl -s -X POST https://cofemon.online/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}' | \
  grep -o '"access_token":"[^"]*"' | cut -d'"' -f4)

curl -s https://cofemon.online/api/auth/me \
  -H "Authorization: Bearer $TOKEN"

# Должен вернуть:
# {"email":"admin@example.com","username":"admin","role":"admin","id":1,...}
```

### 2. Веб-интерфейс
1. Откройте https://cofemon.online/login
2. Войдите: admin / admin123
3. Должно перенаправить на главную страницу

### 3. Логи (если нужно)
```bash
# Проверить логи backend
docker compose logs --tail=50 backend

# Проверить статус всех сервисов
docker compose ps
```

---

## 🔧 Если что-то не работает

### Backend возвращает 401
```bash
# Проверьте что backend пересобрался
docker compose images backend
# Created должна быть свежая дата

# Пересоберите принудительно
docker compose build --no-cache backend
docker compose up -d backend
```

### Frontend не собирается
```bash
# Проверьте файлы
ls -la /root/winget-repo/frontend/src/lib/
# Должны быть: api.ts, auth.tsx, cn.ts

# Пересоберите
docker compose build --no-cache frontend-builder
docker compose up -d frontend-builder
```

---

## 📝 Учетные данные

- **Username**: admin
- **Password**: admin123
- **Email**: admin@example.com

**⚠️ ВАЖНО**: После первого входа смените пароль на безопасный!

---

## 🎯 Что дальше

После успешного деплоя можно:
1. Создать service аккаунт для updater
2. Настроить allow-list для зеркалирования пакетов
3. Настроить автоматическое обновление (updater service)
4. Добавить дополнительных пользователей

---

**Всё протестировано локально и работает. Готово к деплою!** 🚀
