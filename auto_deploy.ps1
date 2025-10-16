# PowerShell script to auto-deploy fixes to server
$ErrorActionPreference = "Stop"

Write-Host "============================================" -ForegroundColor Cyan
Write-Host "AUTO-DEPLOY: Fixing login issue on server" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""

$server = "cofemon.online"
$user = "root"
$password = "GLtr7BsrQ053"

# Commands to run on server
$commands = @"
cd /root/winget-repo && \
echo '--- Pulling latest changes ---' && \
git pull origin main && \
echo '--- Rebuilding backend ---' && \
cd deploy && \
docker compose up -d --build backend && \
echo '--- Waiting for backend to start ---' && \
sleep 20 && \
echo '--- Checking backend status ---' && \
docker compose ps backend && \
echo '--- Running auth test ---' && \
docker compose exec -T backend python test_auth.py
"@

Write-Host "Attempting to connect to $server..." -ForegroundColor Yellow
Write-Host ""
Write-Host "NOTE: This may not work with password authentication." -ForegroundColor Yellow
Write-Host "If it fails, please run the commands manually:" -ForegroundColor Yellow
Write-Host ""
Write-Host "ssh root@cofemon.online" -ForegroundColor Green
Write-Host "# Password: GLtr7BsrQ053" -ForegroundColor Gray
Write-Host ""
Write-Host "Then paste these commands:" -ForegroundColor Yellow
Write-Host $commands -ForegroundColor White
Write-Host ""

# Try using plink if available (PuTTY SSH client for Windows)
if (Get-Command plink -ErrorAction SilentlyContinue) {
    Write-Host "Using plink for SSH connection..." -ForegroundColor Cyan
    echo y | plink -ssh -batch -pw $password "$user@$server" $commands
} else {
    Write-Host "plink not found. Manual execution required." -ForegroundColor Red
    Write-Host ""
    Write-Host "COPY AND RUN THESE COMMANDS ON SERVER:" -ForegroundColor Yellow
    Write-Host "========================================" -ForegroundColor Yellow
    Write-Host $commands
    Write-Host "========================================" -ForegroundColor Yellow
}
