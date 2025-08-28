import os
import redis
from flask import Flask, render_template

app = Flask(__name__)

# Redis连接
try:
    r = redis.Redis(host="redis", port=6379, db=0, decode_responses=True)
    r.ping()
except redis.exceptions.ConnectionError as e:
    print(f"❌ 无法连接到 Redis: {e}")
    r = None

# 配置开发者信息
DEV_INFO = os.getenv('DEV_INFO', '@GenshinImpact_Nahida1027')

@app.route('/')
def index():
    """首页路由"""
    return render_template('index.html', developer=DEV_INFO)

@app.route('/editor')
def editor():
    """问卷编辑器路由"""
    return render_template('editor.html')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)