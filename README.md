# 问答机器人和网页问卷编辑器

这是一个集 Telegram 机器人和网页管理面板于一体的问卷系统，旨在帮助你轻松地创建、管理和分发问卷。

## 核心功能

* **双端管理**: 支持通过 **Telegram 命令**或**网页编辑器**来管理问卷。
* **数据同步**: 任何一端的更改都会实时同步到另一端，因为所有数据都存储在同一个 **Redis 数据库**中。
* **动态问卷**: 支持分支问题和可跳过问题，让问卷逻辑更灵活。
* **用户友好**: 问卷用户可以使用“返回”和“跳过”功能，并且所有回答都会自动发送到你的群组。

---

## 快速部署

### 1. 配置环境变量

在项目根目录创建 `.env` 文件，并根据你的实际情况填写以下信息：

```env
# 你的 Telegram Bot Token
BOT_TOKEN=xxxxxxxxxx:xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# 管理员的 Telegram 用户ID
ADMIN_ID=123456789

# 接收用户问卷回答的群组ID
GROUP_ID=-100xxxxxxxxxx

# 网页编辑器登录口令，请务必设置一个强密码
EDITOR_TOKEN=your_secret_password
2. 启动服务
确保你的服务器已安装 Docker 和 Docker Compose。在项目根目录下，运行以下命令：

docker-compose up -d --build
这会启动三个服务：redis（数据库）、bot（机器人）和 web_panel（网页）。

使用指南
网页端
在浏览器中访问你的服务器 IP 地址：http://<你的服务器IP地址>。

输入你在 .env 中设置的 EDITOR_TOKEN 口令，即可进入编辑器开始管理问卷。

机器人端
在 Telegram 中向你的机器人发送以下命令：

/start: 启动问卷流程。

/end: 结束当前问卷。

/help: 查看所有管理员和用户命令。

管理员命令示例:

/new <目录名>: 创建新问卷。

/addquestion <问题>: 添加一个新问题到当前目录。

/listquestions: 查看所有已有的问卷。
