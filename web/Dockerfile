# 使用官方 Python 运行时作为基础镜像
FROM python:3.11-slim

# 设置工作目录
WORKDIR /app

# 将当前目录内容复制到容器的 /app 目录
COPY . .

# 安装 requirements.txt 文件中指定的任何所需软件包
RUN pip install --no-cache-dir -r requirements.txt

# 使容器的 5000 端口可用
EXPOSE 5000

# 运行 app.py
CMD ["python", "web.py"]
