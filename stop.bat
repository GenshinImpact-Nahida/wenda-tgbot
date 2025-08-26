@echo off
chcp 65001 >nul

echo Stopping Telegram Quiz Bot...

docker compose down
if errorlevel 1 (
    echo 停止失败。请确认 Docker Desktop 已启动后重试。
) else (
    echo 已停止所有服务。
)

pause
