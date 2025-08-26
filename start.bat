@echo off
chcp 65001 >nul

echo Starting Telegram Quiz Bot...

REM 检查 Docker 是否可用
where docker >nul 2>nul || (
    echo ERROR: 未检测到 Docker。请安装 Docker Desktop 并将其加入 PATH。
    echo 下载安装: https://www.docker.com/products/docker-desktop
    pause
    exit /b 1
)

docker --version >nul 2>nul || (
    echo ERROR: Docker 未正确运行。请启动 Docker Desktop 后重试。
    pause
    exit /b 1
)

REM 检查 docker compose 子命令（v2）
docker compose version >nul 2>nul || (
    echo ERROR: 未检测到 "docker compose" 子命令。
    echo 请升级 Docker Desktop 至 4.x+，或改用 docker-compose v1（并相应修改脚本）。
    pause
    exit /b 1
)

echo Building and starting services...
docker compose up -d
if errorlevel 1 (
    echo 启动失败，请检查上方报错信息。
    pause
    exit /b 1
)

echo Waiting for services...
timeout /t 5 /nobreak >nul

echo Services status:
docker compose ps

echo 已成功启动。查看日志: docker compose logs -f bot
pause
