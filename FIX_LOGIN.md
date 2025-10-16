# Исправление проблемы с логином на cofemon.online

## Проблема
При попытке войти в систему через веб-интерфейс возвращается ошибка 401 (Unauthorized).

## Причина
Скорее всего, пользователь admin не был создан в production базе данных на сервере.

## Решение

### Вариант 1: Создать админа через Docker (рекомендуется)

Подключитесь к серверу по SSH и выполните:

```bash
# Подключение к серверу
ssh root@cofemon.online
# Пароль: GLtr7BsrQ053

# Перейдите в директорию проекта
cd /root/winget-repo/deploy

# Создайте admin пользователя
docker compose exec backend python create_admin_auto.py

# Должен вывестись результат:
# ==================================================
# Admin user created successfully!
# ==================================================
# Username: admin
# Email: admin@example.com
# Role: admin
# ID: 1
# Password: admin123
```

### Вариант 2: Если скрипт create_admin_auto.py отсутствует на сервере

```bash
# Подключение к серверу
ssh root@cofemon.online
cd /root/winget-repo

# Получите последние изменения с GitHub
git pull origin main

# Пересоберите backend (включает create_admin_auto.py)
cd deploy
docker compose up -d --build backend

# Подождите, пока backend запустится (15-20 секунд)
sleep 20

# Создайте админа
docker compose exec backend python create_admin_auto.py
```

### Вариант 3: Проверка существующего пользователя

Если пользователь уже существует, но не работает, проверьте:

```bash
# Подключитесь к базе данных
docker compose exec db psql -U winget_user -d winget_db

# Проверьте пользователей
SELECT id, username, email, role, is_active FROM users;

# Если пользователь существует, но is_active = false:
UPDATE users SET is_active = true WHERE username = 'admin';

# Выход из psql
\q
```

### Вариант 4: Полная пересборка (если ничего не помогает)

```bash
cd /root/winget-repo/deploy

# Остановите все контейнеры и удалите volumes
docker compose down -v

# Пересоберите все с нуля
docker compose up -d --build

# Подождите запуска всех сервисов (30-40 секунд)
sleep 40

# Создайте админа
docker compose exec backend python create_admin_auto.py
```

## Проверка

После создания пользователя попробуйте войти:
- URL: https://cofemon.online/login
- Username: `admin`
- Password: `admin123`

## Дополнительная диагностика

Если логин всё равно не работает, проверьте логи:

```bash
# Логи backend
docker compose logs --tail=100 backend | grep -i error

# Логи nginx
docker compose logs --tail=50 nginx

# Статус всех сервисов
docker compose ps
```

## Важно

После первого успешного входа **обязательно смените пароль** через веб-интерфейс или API!

Учетные данные по умолчанию (admin/admin123) небезопасны для production использования.
