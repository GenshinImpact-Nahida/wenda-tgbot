import os
import redis
from flask import Flask, render_template, request, jsonify, redirect, url_for

app = Flask(__name__)

# Redis连接
try:
    r = redis.Redis(host="redis", port=6379, db=0, decode_responses=True)
    r.ping()
    print("✅ 成功连接到 Redis。")
except redis.exceptions.ConnectionError as e:
    print(f"❌ 无法连接到 Redis: {e}")
    r = None # 如果连接失败，将r设置为None，防止后续操作报错

# 配置开发者信息
DEV_INFO = os.getenv('DEV_INFO', '@GenshinImpact_Nahida1027')

# --- 网页路由 ---

@app.route('/')
def index():
    """首页路由"""
    # 首页现在只作为跳转页面，不直接显示问题列表
    return render_template('index.html', developer=DEV_INFO)

@app.route('/editor')
def editor():
    """问卷编辑器路由"""
    # 编辑器页面会通过JS调用API获取数据
    return render_template('editor.html', developer=DEV_INFO)

# --- API 接口路由 ---

@app.route('/api/categories', methods=['GET', 'POST'])
def handle_categories():
    if r is None:
        return jsonify({"error": "Redis连接失败"}), 500

    if request.method == 'GET':
        categories = list(r.smembers("categories"))
        # 附带每个目录的问题数量
        categories_data = []
        for cat in categories:
            question_count = r.scard(f"category_questions:{cat}")
            categories_data.append({"name": cat, "question_count": question_count})
        return jsonify(categories_data)

    elif request.method == 'POST':
        data = request.get_json()
        category_name = data.get('name')
        if not category_name:
            return jsonify({"error": "目录名称不能为空"}), 400
        
        # 检查目录是否已存在
        if r.sismember("categories", category_name):
            return jsonify({"error": "目录已存在"}), 409 # Conflict
            
        r.sadd("categories", category_name)
        return jsonify({"message": f"目录 '{category_name}' 已添加"}), 201

@app.route('/api/categories/<string:category_name>', methods=['DELETE'])
def delete_category(category_name):
    if r is None:
        return jsonify({"error": "Redis连接失败"}), 500
        
    if not r.sismember("categories", category_name):
        return jsonify({"error": "目录不存在"}), 404

    # 删除目录下所有问题
    question_ids = r.smembers(f"category_questions:{category_name}")
    for q_id in question_ids:
        r.delete(f"question:{q_id}")
    r.delete(f"category_questions:{category_name}") # 删除目录-问题关联
    
    # 从总目录列表中删除目录
    r.srem("categories", category_name)
    
    return jsonify({"message": f"目录 '{category_name}' 及其下所有问题已删除"}), 200

@app.route('/api/questions', methods=['GET', 'POST'])
def handle_questions():
    if r is None:
        return jsonify({"error": "Redis连接失败"}), 500

    if request.method == 'GET':
        category_filter = request.args.get('category')
        all_questions = []
        
        if category_filter:
            question_ids = sorted([int(q) for q in r.smembers(f"category_questions:{category_filter}")])
        else: # 如果没有指定目录，则列出所有问题
            question_ids = sorted([int(key.split(':')[1]) for key in r.keys("question:*") if key.startswith("question:")])

        for q_id in question_ids:
            q_data = r.hgetall(f"question:{q_id}")
            if q_data:
                all_questions.append({
                    "id": q_id,
                    "text": q_data.get('text', 'N/A'),
                    "options": q_data.get('options', 'N/A'),
                    "type": q_data.get('type', 'normal'),
                    "skippable": q_data.get('skippable', 'false'),
                    "category": q_data.get('category', 'N/A'),
                    "media_type": q_data.get('media_type', None),
                    "media_id": q_data.get('media_id', None)
                })
        return jsonify(all_questions)

    elif request.method == 'POST':
        data = request.get_json()
        question_text = data.get('text')
        question_category = data.get('category')
        options = data.get('options', '')
        question_type = data.get('type', 'normal') # 'normal' 或 'branch'
        is_skippable = data.get('skippable', False)

        if not question_text or not question_category:
            return jsonify({"error": "问题文本和目录都不能为空"}), 400
        
        if not r.sismember("categories", question_category):
            return jsonify({"error": f"目录 '{question_category}' 不存在，请先创建"}), 400

        try:
            idx = r.incr("question_count")
            
            question_data = {
                "text": question_text,
                "category": question_category,
                "options": options,
                "type": question_type,
                "skippable": "true" if is_skippable else "false"
            }
            # 媒体信息暂不通过网页上传，Bot端负责
            
            r.hmset(f"question:{idx}", question_data)
            r.sadd(f"category_questions:{question_category}", idx) # 关联问题到目录
            
            return jsonify({"message": f"问题 {idx} 已添加至目录 '{question_category}'", "id": idx}), 201
            
        except Exception as e:
            return jsonify({"error": f"添加问题失败: {e}"}), 500

@app.route('/api/questions/<int:question_id>', methods=['DELETE', 'PUT'])
def manage_question(question_id):
    if r is None:
        return jsonify({"error": "Redis连接失败"}), 500

    question_key = f"question:{question_id}"
    if not r.exists(question_key):
        return jsonify({"error": "问题不存在"}), 404

    if request.method == 'DELETE':
        q_data = r.hgetall(question_key)
        category = q_data.get('category')
        
        r.delete(question_key)
        if category:
            r.srem(f"category_questions:{category}", question_id) # 从目录中移除
            
        return jsonify({"message": f"问题 {question_id} 已删除"}), 200

    elif request.method == 'PUT':
        data = request.get_json()
        # 仅允许更新部分字段
        update_fields = ['text', 'options', 'type', 'skippable']
        
        current_q_data = r.hgetall(question_key)
        
        for field in update_fields:
            if field in data:
                if field == 'skippable': # 处理布尔值
                    current_q_data[field] = "true" if data[field] else "false"
                else:
                    current_q_data[field] = data[field]
        
        r.hmset(question_key, current_q_data)
        return jsonify({"message": f"问题 {question_id} 已更新"}), 200

if __name__ == '__main__':
    # Flask应用调试模式下会自动加载环境变量，生产环境需另行处理
    app.run(host='0.0.0.0', port=5000, debug=True)
