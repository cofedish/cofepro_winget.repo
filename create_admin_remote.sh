#!/usr/bin/expect -f
# Автоматический скрипт для создания админа на удаленном сервере

set timeout 30
set password "GLtr7BsrQ053"

# Подключение к серверу
spawn ssh -o StrictHostKeyChecking=no root@cofemon.online

# Ожидание запроса пароля
expect {
    "password:" {
        send "$password\r"
    }
    "Password:" {
        send "$password\r"
    }
}

# Ожидание приглашения командной строки
expect {
    "#" { }
    "$" { }
}

# Переход в директорию проекта
send "cd /root/winget-repo/deploy\r"
expect {
    "#" { }
    "$" { }
}

# Создание админа
send "docker compose exec -T backend python create_admin_auto.py\r"

# Ожидание завершения
expect {
    "Admin user created successfully!" {
        puts "\n=== Админ пользователь успешно создан! ==="
    }
    "Admin user already exists!" {
        puts "\n=== Админ пользователь уже существует ==="
    }
    timeout {
        puts "\n=== Таймаут при создании пользователя ==="
    }
}

# Выход
send "exit\r"
expect eof
