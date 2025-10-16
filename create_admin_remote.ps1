# PowerShell скрипт для создания админа на удаленном сервере
# Использование: .\create_admin_remote.ps1

$password = ConvertTo-SecureString "GLtr7BsrQ053" -AsPlainText -Force
$username = "root"
$hostname = "cofemon.online"

Write-Host "Подключение к серверу $hostname..." -ForegroundColor Yellow

# Создаем команду для выполнения
$command = "cd /root/winget-repo/deploy && docker compose exec -T backend python create_admin_auto.py"

# Выполняем через SSH (требует настроенного SSH клиента Windows)
try {
    # Используем plink если доступен, иначе ssh
    if (Get-Command plink -ErrorAction SilentlyContinue) {
        Write-Host "Используется plink..." -ForegroundColor Cyan
        echo y | plink -ssh -pw "GLtr7BsrQ053" root@cofemon.online "$command"
    } else {
        Write-Host "Используется OpenSSH..." -ForegroundColor Cyan
        # Для OpenSSH на Windows нужен интерактивный ввод или ключи
        Write-Host @"

ВНИМАНИЕ: Автоматический ввод пароля не поддерживается в OpenSSH.

Пожалуйста, выполните команду вручную:

    ssh root@cofemon.online
    # Введите пароль: GLtr7BsrQ053

    cd /root/winget-repo/deploy
    docker compose exec backend python create_admin_auto.py

Или настройте SSH ключи для автоматического подключения.

"@ -ForegroundColor Yellow
    }
} catch {
    Write-Host "Ошибка: $_" -ForegroundColor Red
    Write-Host @"

Пожалуйста, выполните команды вручную:

1. Подключитесь к серверу:
   ssh root@cofemon.online

2. Введите пароль: GLtr7BsrQ053

3. Выполните команды:
   cd /root/winget-repo/deploy
   docker compose exec backend python create_admin_auto.py

"@ -ForegroundColor Yellow
}
