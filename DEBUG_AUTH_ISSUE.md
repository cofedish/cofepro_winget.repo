# Диагностика проблемы с аутентификацией

## Проблема
Логин возвращает 200 и токены, но `/auth/me` возвращает "Could not validate credentials"

## Причина
Скорее всего JWT_SECRET на сервере отличается от того, который использовался при создании токена

## Диагностика на сервере

Выполните команды на сервере:

```bash
cd /root/winget-repo/deploy

# 1. Проверьте JWT_SECRET
grep JWT_SECRET .env

# 2. Проверьте, что backend использует правильный секрет
docker compose exec backend python -c "
from app.config import settings
print('JWT_SECRET (first 10 chars):', settings.jwt_secret[:10])
print('JWT_SECRET length:', len(settings.jwt_secret))
"

# 3. Попробуйте залогиниться и декодировать токен
docker compose exec backend python << 'EOFPYTHON'
import asyncio
from sqlalchemy import select
from app.database import engine
from app.models import User
from app.security import create_access_token, decode_token
from datetime import timedelta

async def test_auth():
    # Получите пользователя
    async with engine.connect() as conn:
        result = await conn.execute(select(User).where(User.username == 'admin'))
        user = result.fetchone()
        if not user:
            print("User not found!")
            return

        print(f"User found: {user.username}, ID: {user.id}, Role: {user.role}")

        # Создайте токен
        token = create_access_token(
            data={"sub": user.id, "role": user.role},
            expires_delta=timedelta(minutes=30)
        )
        print(f"Generated token: {token[:50]}...")

        # Попробуйте декодировать
        try:
            payload = decode_token(token)
            print(f"Token decoded successfully: {payload}")
        except Exception as e:
            print(f"Error decoding token: {e}")

asyncio.run(test_auth())
EOFPYTHON

# 4. Проверьте логи после попытки логина
docker compose logs --tail=50 backend | grep -A 5 -B 5 "auth/me"
```

## Возможные решения

### Решение 1: Убедиться что JWT_SECRET одинаковый (РЕКОМЕНДУЕТСЯ)

1. Проверьте `.env` файл на сервере
2. Убедитесь что JWT_SECRET правильно загружается в backend
3. Перезапустите backend если секрет изменился:
   ```bash
   docker compose restart backend
   ```

### Решение 2: Пересоздать все токены

Если секрет был изменен, все старые токены невалидны. Просто очистите localStorage в браузере и залогиньтесь заново.

### Решение 3: Отладка токена

Скопируйте access_token из ответа логина и декодируйте его на https://jwt.io/ чтобы увидеть payload.

Затем вручную проверьте на сервере:

```bash
docker compose exec backend python << 'EOFPY'
from jose import jwt
from app.config import settings

token = "ВСТАВЬТЕ_ВАШ_ТОКЕН_СЮДА"
try:
    payload = jwt.decode(token, settings.jwt_secret, algorithms=['HS256'])
    print('Success:', payload)
except Exception as e:
    print('Error:', e)
EOFPY
```

## Дополнительная проверка

Проверьте, что backend получает правильный Authorization header:

```bash
# Включите DEBUG логирование
docker compose exec backend python -c "
from app.config import settings
print('Current log level:', settings.log_level)
"

# Временно установите DEBUG=true в .env и перезапустите
echo "DEBUG=true" >> .env
docker compose restart backend
```

После отладки верните DEBUG=false.
