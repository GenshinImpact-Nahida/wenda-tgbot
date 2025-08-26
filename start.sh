#!/bin/bash

echo "🚀 启动 Telegram 问答机器人..."

# 检查环境变量文件
if [ ! -f .env ]; then
    echo "❌ 未找到 .env 文件，请先配置环境变量"
    echo "📝 复制 .env.example 为 .env 并填写配置信息"
    exit 1
fi

# 启动服务
echo "📦 启动 Docker 服务..."
docker-compose up -d

# 等待服务启动
echo "⏳ 等待服务启动..."
sleep 5

# 检查服务状态
echo "🔍 检查服务状态..."
docker-compose ps

echo "✅ 服务启动完成！"
echo "📱 现在可以在 Telegram 中使用机器人了"
echo "📊 查看日志: docker-compose logs -f bot"
