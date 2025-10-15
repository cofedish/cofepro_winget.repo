# Частный репозиторий WinGet

Готовый к промышленной эксплуатации, самостоятельно размещаемый REST-источник WinGet с веб-интерфейсом и автоматическим зеркалированием пакетов.

## Содержание

- [Обзор](#обзор)
- [Архитектура](#архитектура)
- [Возможности](#возможности)
- [Требования](#требования)
- [Быстрый старт](#быстрый-старт)
- [Конфигурация](#конфигурация)
- [Использование](#использование)
- [Настройка клиента WinGet](#настройка-клиента-winget)
- [Безопасность](#безопасность)
- [Устранение неполадок](#устранение-неполадок)
- [Чек-лист перед продакшеном](#чек-лист-перед-продакшеном)
- [Обновления и сопровождение](#обновления-и-сопровождение)
- [Разработка](#разработка)
- [Лицензия](#лицензия)
- [Участие в разработке](#участие-в-разработке)
- [Поддержка](#поддержка)

## Обзор

Этот проект — полноценная, готовая к промышленной эксплуатации реализация частного репозитория WinGet, которая:

- **Реализует API Microsoft.WinGet.Rest.Source** для полной совместимости с клиентом `winget`
- **Предоставляет веб-интерфейс** (React + Vite + Tailwind) для управления пакетами
- **Автоматически зеркалирует пакеты** из публичного WinGet с настраиваемым allow-list
- **Хранит установщики в S3/MinIO** с проверкой SHA-256
- **Работает через полный HTTPS** с реверс-прокси nginx и TLS 1.2/1.3
- **Использует JWT-аутентификацию** с ролевой моделью доступа
- **Хранит данные в PostgreSQL** с миграциями Alembic
- **Разворачивается одной командой** с помощью Docker Compose

## Архитектура

Общая схема компонентов:

```
                 Интернет
                     |
                HTTPS (443)
                     |
           +------------------+
           |   Nginx (TLS)    | <- обратный прокси и rate limiting
           +------------------+
                     |
     +----------------+----------------+
     |                |                |
+-----------+   +-------------+   +---------------+
| Фронтенд  |   |   Бэкенд    |   | WinGet REST   |
|  (React)  |   |  (FastAPI)  |   |      API      |
+-----------+   +-------------+   +---------------+
                     |
     +----------------+----------------+
     |                |                |
+-----------+   +-------------+   +---------------+
|   MinIO   |   | PostgreSQL  |   |   Updater     |
|   (S3)    |   |    (DB)     |   |    Service    |
+-----------+   +-------------+   +---------------+
```

## Возможности

### Основные функции

- **WinGet REST Source API**: полная совместимость с клиентом `winget` (v1.0–1.7)
- **Управление пакетами**: операции создания, изменения и удаления пакетов, версий и установщиков
- **Автозеркалирование**: плановая синхронизация с публичным WinGet и проверкой SHA-256
- **Хранилище файлов**: S3/MinIO для масштабируемого хранения установщиков
- **Потоковые загрузки**: поддержка HTTP Range для больших файлов

### Безопасность

- **Только HTTPS**: TLS 1.2/1.3, HSTS и защитные заголовки
- **Аутентификация JWT**: токены HS256 с механизмом обновления
- **Ролевой доступ**: роли Admin, Maintainer, Viewer, Service
- **Ограничение скорости**: настраиваемые лимиты на уровне эндпоинтов
- **Журнал аудита**: фиксация всех действий с IP и user-agent

### UI и UX

- **Современный веб-интерфейс**: React + Vite + Tailwind + shadcn/ui
- **Тёмная тема**: автоматическое переключение по системным настройкам
- **Адаптивность**: корректная работа на мобильных устройствах
- **Статистика в реальном времени**: дашборд с метриками пакетов

### Эксплуатация

- **Развёртывание одной командой**: `docker compose up -d`
- **Проверки живучести**: встроенные health-checkи
- **Миграции**: управление схемой БД через Alembic
- **Логирование**: JSON-логи для агрегации

## Требования

### Минимальные требования

- **Docker**: 20.10+
- **Docker Compose**: 2.0+
- **SSL-сертификаты**: валидный TLS-сертификат для домена
- **Порты**: 80 (редирект HTTP), 443 (HTTPS)
- **Диск**: 50 ГБ+ под установщики

### Рекомендуется для продакшена

- **CPU**: 4 ядра
- **RAM**: 8 ГБ
- **Диск**: SSD 500 ГБ
- **Сеть**: 100 Мбит/с и выше

## Быстрый старт

### 1. Клонирование репозитория

```bash
git clone <repository-url>
cd winget-repo
```

### 2. Настройка окружения

```bash
cd deploy
cp .env.example .env
nano .env  # отредактируйте конфигурацию
```

**Критически важные параметры:**

```env
# Безопасность — ОБЯЗАТЕЛЬНО изменить
JWT_SECRET=<generate-random-64-char-string>
POSTGRES_PASSWORD=<secure-password>
S3_ACCESS_KEY=<random-access-key>
S3_SECRET_KEY=<random-secret-key>
SERVICE_PASSWORD=<service-account-password>

# Домен
BASE_URL=https://repo.example.com
DOMAIN=repo.example.com
```

### 3. Добавление SSL-сертификатов

Поместите сертификаты в `deploy/certs/`:

```bash
mkdir -p deploy/certs
# Скопируйте свои сертификаты
cp /path/to/fullchain.pem deploy/certs/
cp /path/to/privkey.pem deploy/certs/
```

**Вариант: сгенерировать самоподписанный сертификат для тестирования (НЕ ДЛЯ ПРОДАКШЕНА):**

```bash
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout deploy/certs/privkey.pem \
  -out deploy/certs/fullchain.pem \
  -subj "/CN=repo.example.com"
```

### 4. Запуск сервисов

```bash
cd deploy
docker compose up -d --build
```

**Подождите запуска сервисов (2–3 минуты):**

```bash
docker compose logs -f
```

### 5. Создание администратора

```bash
docker compose exec backend python create_admin.py
```

Следуйте подсказкам или используйте значения по умолчанию:

- Имя пользователя: `admin`
- Пароль: `admin123` (смените сразу!)
- Email: `admin@example.com`

### 6. Создание сервисной учётной записи

```bash
docker compose exec backend python -c "
from app.models import User, UserRole
from app.security import hash_password
from app.database import AsyncSessionLocal
import asyncio

async def create_service():
    async with AsyncSessionLocal() as session:
        user = User(
            username='service',
            email='service@internal',
            password_hash=hash_password('${SERVICE_PASSWORD}'),
            role=UserRole.SERVICE,
            is_active=True
        )
        session.add(user)
        await session.commit()
        print('Service user created')

asyncio.run(create_service())
"
```

### 7. Доступ к веб-интерфейсу

Откройте браузер: `https://repo.example.com`

Войдите с учётными данными администратора.

## Конфигурация

### Переменные окружения

#### Приложение

| Переменная | Описание | Значение по умолчанию |
|-----------|----------|------------------------|
| `APP_NAME` | Название приложения | Private WinGet Repository |
| `BASE_URL` | Публичный URL | https://repo.example.com |
| `DEBUG` | Режим отладки | false |
| `ENVIRONMENT` | Тип окружения | production |

#### Безопасность

| Переменная | Описание | Обязательно |
|-----------|----------|-------------|
| `JWT_SECRET` | Ключ подписи JWT (минимум 32 символа) | да |
| `JWT_ACCESS_TOKEN_EXPIRE_MINUTES` | Время жизни access-токена | нет (30) |
| `JWT_REFRESH_TOKEN_EXPIRE_DAYS` | Время жизни refresh-токена | нет (7) |

#### База данных

| Переменная | Описание | Значение по умолчанию |
|-----------|----------|------------------------|
| `POSTGRES_HOST` | Хост PostgreSQL | db |
| `POSTGRES_PORT` | Порт PostgreSQL | 5432 |
| `POSTGRES_DB` | Имя базы данных | winget_repo |
| `POSTGRES_USER` | Пользователь базы данных | winget |
| `POSTGRES_PASSWORD` | Пароль базы данных | — |

#### S3/MinIO

| Переменная | Описание | Значение по умолчанию |
|-----------|----------|------------------------|
| `S3_ENDPOINT` | URL эндпоинта S3 | http://minio:9000 |
| `S3_REGION` | Регион S3 | us-east-1 |
| `S3_BUCKET` | Название бакета | winget-installers |
| `S3_ACCESS_KEY` | Access key | — |
| `S3_SECRET_KEY` | Secret key | — |
| `S3_SECURE` | Использовать HTTPS | false (true для внешнего S3) |
| `S3_FORCE_PATH_STYLE` | Путь в стиле path | true (требуется для MinIO) |

#### Updater

| Переменная | Описание | Значение по умолчанию |
|-----------|----------|------------------------|
| `UPDATER_INTERVAL_MINUTES` | Интервал синхронизации | 60 |
| `UPDATER_MAX_VERSIONS_PER_PACKAGE` | Максимум версий на пакет | 5 |
| `UPDATER_ARCHITECTURES` | Разрешённые архитектуры | x64,x86 |
| `UPDATER_INSTALLER_TYPES` | Разрешённые типы установщиков | exe,msi,msix |
| `ALLOWLIST_PATH` | Путь к allow-list | /app/allow-list.json |

### Настройка списка разрешённых пакетов

Измените `updater/allow-list.json`, чтобы указать пакеты для зеркалирования:

```json
{
  "packages": [
    {
      "package_identifier": "7zip.7zip",
      "architectures": ["x64", "x86"],
      "installer_types": ["exe", "msi"],
      "max_versions": 3
    },
    {
      "package_identifier": "VideoLAN.VLC",
      "architectures": ["x64"],
      "installer_types": ["msi"],
      "max_versions": 2
    }
  ]
}
```

**После изменения перезапустите updater:**

```bash
docker compose restart updater
```

### Внешний S3 (AWS/DigitalOcean и др.)

Чтобы использовать внешний S3 вместо MinIO, обновите `.env`:

```env
S3_ENDPOINT=https://s3.us-east-1.amazonaws.com
S3_REGION=us-east-1
S3_BUCKET=my-winget-bucket
S3_ACCESS_KEY=<aws-access-key>
S3_SECRET_KEY=<aws-secret-key>
S3_SECURE=true
S3_FORCE_PATH_STYLE=false
```

Затем закомментируйте сервисы `minio` и `minio-init` в `docker-compose.yml`.

## Использование

### Веб-интерфейс

1. **Dashboard**: статистика и краткое руководство
2. **Packages**: просмотр, поиск и управление пакетами
3. **Upload**: ручная загрузка установщиков для приватных пакетов
4. **Settings**: настройка allow-list и просмотр журнала аудита
5. **Users**: управление пользователями и правами (только администратор)

### Точки API

#### Точки клиента WinGet

- `GET /information` — информация об источнике
- `POST /manifestSearch` — поиск пакетов
- `GET /packageManifests/{id}` — получение манифеста
- `GET /packageManifests/{id}/{version}` — манифест конкретной версии
- `GET /packageVersions/{id}` — список версий
- `GET /dl/{s3-key}` — загрузка установщика

#### Административный API

- `GET /api/admin/packages` — список пакетов
- `POST /api/admin/packages` — создание пакета
- `GET /api/admin/packages/{id}` — детали пакета
- `PUT /api/admin/packages/{id}` — обновление пакета
- `DELETE /api/admin/packages/{id}` — удаление пакета
- `POST /api/admin/upload` — загрузка установщика
- `POST /api/admin/upload-from-url` — загрузка по URL
- `GET /api/admin/dashboard/stats` — статистика для дашборда
- `GET /api/admin/audit-logs` — журнал аудита

#### Аутентификация

- `POST /api/auth/login` — вход
- `POST /api/auth/refresh` — обновление токена
- `GET /api/auth/me` — сведения о текущем пользователе

### Ручная загрузка пакета

1. Войдите в веб-интерфейс
2. Перейдите на страницу «Upload»
3. Создайте пакет (если его ещё нет)
4. Создайте версию
5. Загрузите файл установщика или укажите URL
6. Система посчитает SHA-256 и сохранит файл в S3

### Принудительная синхронизация

```bash
# Перезапустите updater для немедленной синхронизации
docker compose restart updater

# Или войдите в контейнер updater и запустите вручную
docker compose exec updater python main.py
```

## Настройка клиента WinGet

### Добавить приватный источник

```powershell
winget source add -n Private -t Microsoft.Rest -a https://repo.example.com
```

### Поиск пакетов

```powershell
winget search 7zip --source Private
```

### Показать информацию о пакете

```powershell
winget show 7zip.7zip --source Private
```

### Установить пакет

```powershell
winget install 7zip.7zip --source Private
```

### Показать список источников

```powershell
winget source list
```

### Удалить источник

```powershell
winget source remove -n Private
```

### Диагностика WinGet

**Проблемы с доверием к сертификату:**

Если используется самоподписанный или корпоративный сертификат, установите корневой сертификат:

```powershell
# Импорт корневого сертификата
Import-Certificate -FilePath "ca-cert.crt" -CertStoreLocation Cert:\LocalMachine\Root
```

**Настройки WinGet:**

Отредактируйте `%LOCALAPPDATA%\Packages\Microsoft.DesktopAppInstaller_8wekyb3d8bbwe\LocalState\settings.json`:

```json
{
  "experimentalFeatures": {
    "experimentalMSStore": false
  },
  "network": {
    "downloader": "wininet",
    "doProgressTimeoutInSeconds": 300
  }
}
```

**Настройка прокси:**

```powershell
# Установка прокси для WinGet
netsh winhttp set proxy proxy-server="http://proxy.example.com:8080"
```

**Отладка:**

```powershell
# Включить подробное логирование
winget install 7zip.7zip --source Private --verbose-logs

# Просмотр логов
%LOCALAPPDATA%\Packages\Microsoft.DesktopAppInstaller_8wekyb3d8bbwe\LocalState\DiagOutputDir
```

## Безопасность

### Настройка HTTPS

**Для продакшена требуются валидные SSL-сертификаты.** Варианты:

#### 1. Let's Encrypt (Certbot)

Добавьте сервис certbot в `docker-compose.yml`:

```yaml
certbot:
  image: certbot/certbot
  volumes:
    - ./certs:/etc/letsencrypt
  command: certonly --webroot -w /var/www/certbot -d repo.example.com --email admin@example.com --agree-tos --non-interactive
```

#### 2. Корпоративный центр сертификации

Поместите сертификаты в `deploy/certs/`:

```bash
cp corporate-fullchain.pem deploy/certs/fullchain.pem
cp corporate-privkey.pem deploy/certs/privkey.pem
```

#### 3. Wildcard-сертификат

Если используется wildcard-сертификат (*.example.com), просто положите файлы в `deploy/certs/`.

### Заголовки безопасности

Nginx автоматически добавляет:

- `Strict-Transport-Security`: HSTS с max-age 2 года
- `X-Frame-Options`: SAMEORIGIN
- `X-Content-Type-Options`: nosniff
- `X-XSS-Protection`: 1; mode=block
- `Referrer-Policy`: no-referrer-when-downgrade

### Ограничение скорости

Лимиты по умолчанию (можно настроить в `nginx.conf`):

- API: 60 запросов в минуту
- Поиск: 30 запросов в минуту

### Аутентификация

- **JWT-токены**: алгоритм HS256
- **Access-токены**: срок жизни 30 минут
- **Refresh-токены**: срок жизни 7 дней
- **Хеширование паролей**: bcrypt

### Роли и права

| Роль | Права |
|------|-------|
| **Admin** | Полный доступ, управление пользователями, удаление |
| **Maintainer** | Создание/обновление пакетов, загрузка установщиков |
| **Viewer** | Только чтение пакетов |
| **Service** | Внутренняя учётная запись для updater |

### Аудит событий

Все действия пишутся в базу данных:

- Пользователь
- Действие (create/update/delete/upload)
- Объект (package/version/installer/user)
- Метаданные (внесённые изменения)
- IP-адрес и user-agent
- Время

Просматривать журнал можно в веб-интерфейсе (Admin > Audit Logs).

## Устранение неполадок

### Сервис не запускается

```bash
# Просмотр логов
docker compose logs backend
docker compose logs nginx

# Проверка статуса сервисов
docker compose ps

# Перезапуск конкретного сервиса
docker compose restart backend
```

### Проблемы с подключением к базе данных

```bash
# Проверка, что БД запущена
docker compose ps db

# Тестовое подключение
docker compose exec db psql -U winget -d winget_repo -c "SELECT 1"

# Просмотр логов БД
docker compose logs db
```

### Проблемы с MinIO/S3

```bash
# Проверка статуса MinIO
docker compose ps minio

# Доступ к консоли MinIO
# http://localhost:9001 (в браузере)
# Логин: S3_ACCESS_KEY / S3_SECRET_KEY из .env

# Список бакетов
docker compose exec minio mc ls myminio
```

### Updater не синхронизирует

```bash
# Просмотр логов updater
docker compose logs updater -f

# Проверка allow-list
cat updater/allow-list.json

# Ручной запуск
docker compose restart updater

# Проверка сервисной учётной записи
docker compose exec backend python -c "
from app.models import User
from app.database import AsyncSessionLocal
import asyncio

async def check():
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(User).where(User.username == 'service'))
        user = result.scalar_one_or_none()
        print(f'Сервисный пользователь: {user.username if user else "НЕ НАЙДЕН"}')

asyncio.run(check())
"
```

### Клиент WinGet не может подключиться

1. **Проверьте HTTPS:**

```bash
curl -v https://repo.example.com/information
```

2. **Проверьте сертификат:**

```bash
openssl s_client -connect repo.example.com:443 -servername repo.example.com
```

3. **Проверьте с Windows:**

```powershell
# Проверка соединения
Test-NetConnection -ComputerName repo.example.com -Port 443

# Тест HTTP-запроса
Invoke-WebRequest -Uri https://repo.example.com/information
```

4. **Проверьте источник WinGet:**

```powershell
winget source list
winget source reset --force
```

### Сборка фронтенда завершается с ошибкой

```bash
# Пересобрать фронтенд
docker compose up -d --build frontend-builder

# Просмотреть логи
docker compose logs frontend-builder
```

### Высокое потребление памяти

```bash
# Проверка использования ресурсов
docker stats

# Ограничьте число воркеров бэкенда (в docker-compose.yml)
# Измените: --workers 4 -> --workers 2

# Перезапуск сервисов
docker compose restart
```

## Чек-лист перед продакшеном

Перед запуском убедитесь, что выполнено:

- [ ] **Сменены пароли по умолчанию** в `.env`
- [ ] **Сгенерирован сильный JWT_SECRET** (минимум 64 символа)
- [ ] **Установлены валидные SSL-сертификаты**
- [ ] **Настроен файрвол** (разрешены только 80/443)
- [ ] **Настроено резервное копирование** PostgreSQL и MinIO
- [ ] **Настроен мониторинг** (Prometheus/Grafana)
- [ ] **Включена агрегация логов** (ELK/Loki)
- [ ] **Проверены лимиты** в `nginx.conf`
- [ ] **Тесты клиента WinGet** выполнены на рабочих станциях
- [ ] **Описаны процедуры восстановления**
- [ ] **Настроены оповещения** об отказах сервисов
- [ ] **Проверен allow-list** пакетов
- [ ] **Протестировано восстановление из бэкапа**
- [ ] **Настроено автоматическое продление сертификатов**
- [ ] **Проверены защитные заголовки** в nginx
- [ ] **Включена 2FA** для администраторов (план развития)

### Стратегия резервного копирования

**База данных:**

```bash
# Бэкап
docker compose exec db pg_dump -U winget winget_repo > backup-$(date +%Y%m%d).sql

# Восстановление
cat backup-20240115.sql | docker compose exec -T db psql -U winget -d winget_repo
```

**MinIO:**

```bash
# Бэкап
docker compose exec minio mc mirror myminio/winget-installers /backup/minio-$(date +%Y%m%d)

# Или используйте встроенную репликацию MinIO в другой бакет
```

**Автоматические бэкапы:**

Добавьте cron на хосте:

```bash
# /etc/cron.daily/winget-backup.sh
#!/bin/bash
cd /path/to/winget-repo/deploy
docker compose exec db pg_dump -U winget winget_repo | gzip > /backups/db-$(date +%Y%m%d).sql.gz
docker compose exec minio mc mirror myminio/winget-installers /backups/minio-$(date +%Y%m%d)
# Загрузка на S3/удалённое хранилище
find /backups -mtime +30 -delete  # храним 30 дней
```

### Мониторинг

**Health-check эндпоинты:**

- Бэкенд: `https://repo.example.com/health`
- База данных: проверяется через health-бэкенда
- MinIO: `http://minio:9000/minio/health/live`

**Метрики для мониторинга:**

- Время ответа HTTP
- Пул подключений к БД
- Свободное место (особенно том MinIO)
- Память по контейнерам
- Ошибки API
- Успех/ошибка установок WinGet

**Пример конфигурации Prometheus:**

```yaml
scrape_configs:
  - job_name: 'winget-repo'
    static_configs:
      - targets: ['repo.example.com:443']
    scheme: https
    metrics_path: /metrics  # добавьте эндпоинт метрик в бэкенд
```

### Управление логами

**Просмотр логов:**

```bash
# Все сервисы
docker compose logs -f

# Конкретный сервис
docker compose logs -f backend

# С таймстампами
docker compose logs -f --timestamps backend

# Последние 100 строк
docker compose logs --tail=100 backend
```

**Ротация логов (на хосте):**

```bash
# /etc/docker/daemon.json
{
  "log-driver": "json-file",
  "log-opts": {
    "max-size": "10m",
    "max-file": "3"
  }
}
```

## Обновления и сопровождение

### Обновление сервисов

```bash
# Получить последние образы
docker compose pull

# Пересобрать и перезапустить
docker compose up -d --build

# Проверить наличие ошибок
docker compose logs -f
```

### Миграции базы данных

```bash
# Создать миграцию
docker compose exec backend alembic revision --autogenerate -m "description"

# Применить миграции
docker compose exec backend alembic upgrade head

# Откат
docker compose exec backend alembic downgrade -1
```

### Масштабирование

**Горизонтальное масштабирование (несколько воркеров бэкенда):**

```yaml
# docker-compose.yml
backend:
  deploy:
    replicas: 3
```

**Вертикальное масштабирование:**

```yaml
# docker-compose.yml
backend:
  deploy:
    resources:
      limits:
        cpus: '2'
        memory: 4G
```

## Разработка

### Локальная разработка

```bash
# Бэкенд
cd backend
python -m venv venv
source venv/bin/activate  # или venv\Scripts\activate на Windows
pip install -r requirements.txt
uvicorn app.main:app --reload

# Фронтенд
cd frontend
npm install
npm run dev

# Updater
cd updater
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python main.py
```

### Тестирование

```bash
# Тесты бэкенда
cd backend
pytest

# API-тест
curl -X POST https://repo.example.com/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}'
```

### Качество кода

```bash
# Проверка Python
ruff check backend/
black backend/

# Проверка TypeScript
cd frontend
npm run lint
```

## Лицензия

[Укажите вашу лицензию здесь]

## Участие в разработке

1. Форкните репозиторий
2. Создайте ветку с фичей
3. Сделайте коммит
4. Запушьте ветку
5. Создайте Pull Request

## Поддержка

- **Задачи**: [GitHub Issues]
- **Обсуждения**: [GitHub Discussions]
- **Документация**: этот README

---

**Сделано с ❤️ для сообщества WinGet**
