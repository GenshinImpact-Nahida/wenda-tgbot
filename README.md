# Telegram 问答机器人

一个功能完整的 Telegram 问答机器人，支持动态配置问题、多种答案类型、话题管理和**智能分支逻辑**。

## 功能特性

- 🤖 **动态问题管理**: 管理员可以随时添加、删除、查看问题
- 🎯 **多种答案类型**: 支持文本、图片、视频、文档等
- 🧵 **话题管理**: 每个用户的答案在独立话题中展示
- 📊 **进度跟踪**: 实时显示用户答题进度
- 🌳 **智能分支**: 根据用户答案导向不同的问题路径
- 🐳 **Docker 部署**: 开箱即用，支持一键部署

## 快速开始

### 1. 环境准备

- 创建 Telegram Bot（通过 @BotFather）
- 获取你的 Telegram 用户 ID
- 创建一个群组并获取群组 ID

### 2. 配置环境变量

复制 `env.example` 为 `.env` 并填写：

```bash
BOT_TOKEN=你的TG机器人TOKEN
ADMIN_ID=你的TG用户ID
GROUP_ID=你的群组ID
```

### 3. 启动服务

```bash
docker-compose up -d
```

### 4. 配置问题

在 Telegram 中向机器人发送：

#### 普通问题
```
/addquestion 请描述你最喜欢的电影
/addquestion 上传一张你最喜欢的照片
```

#### 选择题
```
/addquestion 你最喜欢的颜色？|红色,蓝色,绿色
/addquestion 你的年龄段是？|18岁以下,18-25岁,26-35岁,35岁以上
```

#### 🆕 分支问题（新功能！）
```
/addbranch 你喜欢的颜色？|红色:3,蓝色:5,绿色:7
/addbranch 你的职业是？|学生:10,上班族:15,自由职业:20
```

**分支问题说明：**
- 使用 `/addbranch` 创建分支问题
- 格式：`问题|选项1:下一题ID,选项2:下一题ID`
- 用户选择不同选项会跳转到不同的问题
- 例如：选择"红色"会跳转到第3题，选择"蓝色"会跳转到第5题

## 管理员命令

- `/addquestion 问题|选项1,选项2,选项3` - 添加普通问题
- `/addbranch 问题|选项1:下一题ID,选项2:下一题ID` - 添加分支问题
- `/listquestions` - 列出所有问题
- `/clearall` - 清空所有问题

## 用户命令

- `/start` - 开始答题
- `/status` - 查看答题进度
- `/help` - 显示帮助信息

## 分支逻辑示例

### 示例1：颜色偏好分支
```
/addquestion 你好！请开始答题
/addbranch 你最喜欢的颜色？|红色:3,蓝色:4,绿色:5
/addquestion 你喜欢红色的什么？
/addquestion 你喜欢蓝色的什么？
/addquestion 你喜欢绿色的什么？
```

### 示例2：职业相关分支
```
/addquestion 欢迎参加问卷调查
/addbranch 你的职业是？|学生:3,上班族:6,自由职业:9
/addquestion 你在哪个学校读书？
/addquestion 你在哪个公司工作？
/addquestion 你从事什么自由职业？
```

## 项目结构

```
telegram-quiz-bot/
├── bot.py              # 主要机器人代码
├── requirements.txt    # Python 依赖
├── Dockerfile         # Docker 镜像构建
├── docker-compose.yml # Docker 编排配置
├── env.example        # 环境变量示例
├── start.sh           # Linux/Mac 启动脚本
├── start.bat          # Windows 启动脚本
├── stop.sh            # Linux/Mac 停止脚本
├── stop.bat           # Windows 停止脚本
├── README.md          # 项目说明
├── QUICK_START.md     # 快速开始指南
└── .gitignore         # Git 忽略文件
```

## 技术架构

- **框架**: Python + Aiogram 3.x
- **存储**: Redis
- **部署**: Docker + Docker Compose
- **异步**: 全异步架构，高性能处理
- **分支逻辑**: 智能路由系统，支持复杂问答流程

## 注意事项

1. 确保群组已开启话题功能（Forum）
2. 机器人需要管理员权限来创建话题
3. Redis 数据会持久化保存
4. 支持热重启，无需停止服务即可更新问题
5. **分支问题会根据用户选择跳转，确保目标问题ID存在**

## 故障排除

### 常见问题

1. **话题创建失败**: 检查机器人是否有管理员权限
2. **Redis 连接失败**: 确保 Redis 服务正常运行
3. **权限不足**: 确认 ADMIN_ID 设置正确
4. **分支跳转失败**: 检查目标问题ID是否存在，确认选项格式正确

### 日志查看

```bash
docker-compose logs -f bot
```

## 许可证

MIT License
