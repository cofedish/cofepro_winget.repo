# Настройка SSH ключей для автоматического подключения

## Зачем это нужно?
SSH ключи позволяют подключаться к серверу без ввода пароля, что удобно для автоматизации.

## Шаги настройки

### 1. Создайте SSH ключ (если еще нет)

```bash
# В Git Bash или PowerShell
ssh-keygen -t ed25519 -C "winget-repo-deploy"

# Нажмите Enter для сохранения в ~/.ssh/id_ed25519
# Можете задать пароль или оставить пустым для автоматизации
```

### 2. Скопируйте публичный ключ на сервер

**Способ A: Автоматически (если ssh-copy-id доступен)**
```bash
ssh-copy-id -i ~/.ssh/id_ed25519.pub root@cofemon.online
# Введите пароль: GLtr7BsrQ053
```

**Способ B: Вручную**
```bash
# 1. Покажите публичный ключ
cat ~/.ssh/id_ed25519.pub
# Скопируйте вывод

# 2. Подключитесь к серверу
ssh root@cofemon.online
# Пароль: GLtr7BsrQ053

# 3. Добавьте ключ в authorized_keys
mkdir -p ~/.ssh
chmod 700 ~/.ssh
echo "ВСТАВЬТЕ_СКОПИРОВАННЫЙ_КЛЮЧ" >> ~/.ssh/authorized_keys
chmod 600 ~/.ssh/authorized_keys
exit
```

### 3. Проверьте подключение

```bash
ssh root@cofemon.online "echo 'SSH ключ работает!'"
# Должно подключиться без запроса пароля
```

## После настройки ключей

Вы сможете выполнять команды на сервере автоматически:

```bash
# Создание админа
ssh root@cofemon.online "cd /root/winget-repo/deploy && docker compose exec -T backend python create_admin_auto.py"

# Проверка логов
ssh root@cofemon.online "cd /root/winget-repo/deploy && docker compose logs --tail=50 backend"

# Перезапуск сервисов
ssh root@cofemon.online "cd /root/winget-repo/deploy && docker compose restart backend"
```
