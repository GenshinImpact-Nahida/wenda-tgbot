import os
import redis
from flask import Flask, render_template, request, redirect, url_for

app = Flask(__name__)

# Redis连接
r = redis.Redis(host="redis", port=6379, db=0, decode_responses=True)

@app.route('/')
def index():
    success = request.args.get('success')
    return render_template('index.html', success=success)

@app.route('/add', methods=['POST'])
def add_question():
    question_text = request.form.get('question_text')
    options = request.form.get('options')
    question_type = request.form.get('question_type')
    is_skippable = request.form.get('is_skippable') == 'on'

    if not question_text:
        return "问题文本不能为空", 400

    try:
        idx = r.incr("question_count")
        
        question_data = {
            "text": question_text,
            "skippable": "true" if is_skippable else "false"
        }

        if options:
            question_data['options'] = options
        
        if question_type == 'branch':
            question_data['type'] = 'branch'
            
        r.hmset(f"question:{idx}", question_data)
        
        return redirect(url_for('index', success=True))
    
    except Exception as e:
        return f"添加问题失败: {e}", 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)