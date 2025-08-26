#!/bin/bash

echo "🛑 停止 Telegram 问答机器人..."

# 停止服务
docker-compose down

echo "✅ 服务已停止"
echo "💾 Redis 数据已保存"
