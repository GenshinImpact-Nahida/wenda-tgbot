# 🚀 快速开始指南

## 📋 准备工作

### 1. 创建 Telegram Bot
1. 在 Telegram 中找到 @BotFather
2. 发送 `/newbot` 命令
3. 按提示设置机器人名称和用户名
4. 保存获得的 `BOT_TOKEN`

### 2. 获取你的用户 ID
1. 在 Telegram 中找到 @userinfobot
2. 发送任意消息
3. 保存获得的用户 ID

### 3. 创建群组并获取群组 ID
1. 创建一个新群组
2. 将你的机器人添加到群组
3. 给机器人管理员权限
4. 开启群组的话题功能（Forum）
5. 在群组中发送 `/id` 或使用 @userinfobot 获取群组 ID

## ⚙️ 配置环境

### 1. 复制环境变量文件
```bash
# Linux/Mac
cp env.example .env

# Windows
copy env.example .env
```

### 2. 编辑 .env 文件
```bash
BOT_TOKEN=你的TG机器人TOKEN
ADMIN_ID=你的TG用户ID
GROUP_ID=你的群组ID
```

## 🐳 启动服务

### 使用 Docker Compose
```bash
# 启动
docker-compose up -d

# 查看状态
docker-compose ps

# 查看日志
docker-compose logs -f bot

# 停止
docker-compose down
```

### 使用脚本
```bash
# Linux/Mac
./start.sh

# Windows
start.bat
```

## 📝 配置问题

在 Telegram 中向机器人发送以下命令：

### 添加普通问题
```
/addquestion 请描述你最喜欢的电影
/addquestion 上传一张你最喜欢的照片
/addquestion 请分享你的兴趣爱好
```

### 添加选择题
```
/addquestion 你的年龄段是？|18岁以下,18-25岁,26-35岁,35岁以上
/addquestion 你最喜欢的运动？|足球,篮球,网球,游泳
```

### 🆕 添加分支问题（新功能！）
```
/addbranch 你喜欢的颜色？|红色:3,蓝色:5,绿色:7
/addbranch 你的职业是？|学生:10,上班族:15,自由职业:20
/addbranch 你更喜欢哪种音乐？|流行:25,摇滚:30,古典:35
```

**分支问题说明：**
- 使用 `/addbranch` 创建分支问题
- 格式：`问题|选项1:下一题ID,选项2:下一题ID`
- 用户选择不同选项会跳转到不同的问题
- 例如：选择"红色"会跳转到第3题，选择"蓝色"会跳转到第5题

## 🧪 测试机器人

1. 用户发送 `/start` 开始答题
2. 机器人会依次发送问题
3. 用户可以选择按钮或输入文本回答
4. 支持上传图片、视频、文档等
5. **分支问题会根据用户选择导向不同路径**
6. 所有答案会自动转发到群组的话题中

## 🔧 常用命令

### 管理员命令
- `/addquestion 问题|选项1,选项2,选项3` - 添加普通问题
- `/addbranch 问题|选项1:下一题ID,选项2:下一题ID` - 添加分支问题
- `/listquestions` - 查看所有问题
- `/clearall` - 清空所有问题
- `/help` - 显示帮助

### 用户命令
- `/start` - 开始答题
- `/status` - 查看进度
- `/help` - 显示帮助

## 🌳 分支问题示例

### 示例1：简单的颜色分支
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

### 示例3：兴趣爱好分支
```
/addquestion 让我们了解一下你的兴趣爱好
/addbranch 你更喜欢哪种活动？|室内:3,户外:6,运动:9
/addquestion 你最喜欢的室内活动是什么？
/addquestion 你最喜欢的户外活动是什么？
/addquestion 你最喜欢的运动是什么？
```

## ❗ 注意事项

1. **群组设置**: 确保群组已开启话题功能
2. **机器人权限**: 机器人需要管理员权限来创建话题
3. **Redis 数据**: 数据会自动持久化保存
4. **热重启**: 修改问题后无需重启服务
5. **分支逻辑**: 分支问题会根据用户选择跳转，确保目标问题ID存在

## 🆘 故障排除

### 常见问题

1. **话题创建失败**
   - 检查机器人是否有管理员权限
   - 确认群组已开启话题功能

2. **Redis 连接失败**
   - 检查 Docker 服务是否正常运行
   - 查看 `docker-compose logs redis`

3. **权限不足**
   - 确认 ADMIN_ID 设置正确
   - 检查环境变量文件格式

4. **分支跳转失败**
   - 检查目标问题ID是否存在
   - 确认选项格式正确（选项:ID）

### 查看日志
```bash
# 查看机器人日志
docker-compose logs -f bot

# 查看 Redis 日志
docker-compose logs -f redis

# 查看所有服务状态
docker-compose ps
```

## 📚 更多信息

- 详细文档: [README.md](README.md)
- 项目结构: 查看项目根目录
- 技术支持: 查看日志和错误信息
