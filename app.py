from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from config import Config
from utils.rag_engine import RAGEngine
from utils.auth import Auth
from utils.document_parser import DocumentParser
import os

app = Flask(__name__, static_folder='static', static_url_path='/static')
app.secret_key = Config.SECRET_KEY

# 初始化组件
auth = Auth()
rag_engine = RAGEngine()
doc_parser = DocumentParser()

# ==================== 页面路由 ====================

@app.route('/')
def index():
    if 'user' not in session:
        return redirect(url_for('login'))
    return render_template('index.html')

@app.route('/login')
def login():
    return render_template('login.html')

@app.route('/register')
def register():
    return render_template('register.html')

@app.route('/admin/codes')
def admin_codes():
    """激活码管理页面"""
    if 'user' not in session:
        return redirect(url_for('login'))
    user_info = auth.get_user_info(session['user'])
    if not user_info or user_info['role'] != 'admin':
        return "权限不足", 403
    return render_template('admin_codes.html')

@app.route('/admin/users')
def admin_users():
    """用户管理页面"""
    if 'user' not in session:
        return redirect(url_for('login'))
    user_info = auth.get_user_info(session['user'])
    if not user_info or user_info['role'] != 'admin':
        return "权限不足", 403
    return render_template('admin_users.html')

# ==================== API路由 ====================

@app.route('/api/login', methods=['POST'])
def api_login():
    data = request.json
    username = data.get('username')
    password = data.get('password')
    result = auth.verify_user(username, password)
    if result:
        session['user'] = username
        return jsonify({'success': True, 'message': '登录成功', 'role': result['role']})
    return jsonify({'success': False, 'message': '用户名或密码错误'})

@app.route('/api/logout')
def logout():
    session.pop('user', None)
    return jsonify({'success': True})

@app.route('/api/register', methods=['POST'])
def api_register():
    """用户注册API（需要激活码）"""
    data = request.json
    username = data.get('username', '').strip()
    email = data.get('email', '').strip()
    password = data.get('password', '')
    invite_code = data.get('invite_code', '').strip()
    
    # 验证输入
    if not username or len(username) < 3 or len(username) > 20:
        return jsonify({'success': False, 'message': '用户名长度应为3-20个字符'})
    
    if not password or len(password) < 6:
        return jsonify({'success': False, 'message': '密码长度至少6位'})
    
    if not invite_code:
        return jsonify({'success': False, 'message': '请填写激活码'})
    
    # 注册用户
    result = auth.register_user(username, password, email, invite_code)
    return jsonify(result)

@app.route('/api/chat', methods=['POST'])
def chat():
    if 'user' not in session:
        return jsonify({'success': False, 'message': '请先登录'})
    data = request.json
    question = data.get('question', '')
    if not question:
        return jsonify({'success': False, 'message': '问题不能为空'})
    try:
        answer = rag_engine.query(question)
        return jsonify({'success': True, 'answer': answer})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/upload', methods=['POST'])
def upload_file():
    if 'user' not in session:
        return jsonify({'success': False, 'message': '请先登录'})
    if 'file' not in request.files:
        return jsonify({'success': False, 'message': '没有上传文件'})
    file = request.files['file']
    if file.filename == '':
        return jsonify({'success': False, 'message': '没有选择文件'})
    try:
        content = doc_parser.parse_file(file)
        rag_engine.add_document(file.filename, content)
        return jsonify({'success': True, 'message': '文件上传并解析成功'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

# ==================== 管理员API ====================

@app.route('/api/admin/generate-code', methods=['POST'])
def api_generate_code():
    """生成激活码（管理员）"""
    if 'user' not in session:
        return jsonify({'success': False, 'message': '请先登录'})
    
    user_info = auth.get_user_info(session['user'])
    if not user_info or user_info['role'] != 'admin':
        return jsonify({'success': False, 'message': '权限不足'})
    
    data = request.json
    count = data.get('count', 10)
    
    if count < 1 or count > 100:
        return jsonify({'success': False, 'message': '数量必须在1-100之间'})
    
    codes = auth.generate_invite_codes(count, session['user'])
    return jsonify({'success': True, 'codes': codes, 'count': len(codes)})

@app.route('/api/admin/codes', methods=['GET'])
def api_get_codes():
    """获取激活码列表（管理员）"""
    if 'user' not in session:
        return jsonify({'success': False, 'message': '请先登录'})
    
    user_info = auth.get_user_info(session['user'])
    if not user_info or user_info['role'] != 'admin':
        return jsonify({'success': False, 'message': '权限不足'})
    
    status = request.args.get('status')
    codes = auth.get_invite_codes(status)
    return jsonify({'success': True, 'codes': codes})

@app.route('/api/admin/codes/<int:code_id>', methods=['DELETE'])
def api_delete_code(code_id):
    """删除激活码（管理员）"""
    if 'user' not in session:
        return jsonify({'success': False, 'message': '请先登录'})
    
    user_info = auth.get_user_info(session['user'])
    if not user_info or user_info['role'] != 'admin':
        return jsonify({'success': False, 'message': '权限不足'})
    
    result = auth.delete_invite_code(code_id)
    if result:
        return jsonify({'success': True, 'message': '删除成功'})
    return jsonify({'success': False, 'message': '删除失败'})

@app.route('/api/admin/users', methods=['GET'])
def api_get_users():
    """获取用户列表（管理员）"""
    if 'user' not in session:
        return jsonify({'success': False, 'message': '请先登录'})
    
    user_info = auth.get_user_info(session['user'])
    if not user_info or user_info['role'] != 'admin':
        return jsonify({'success': False, 'message': '权限不足'})
    
    users = auth.list_users()
    return jsonify({'success': True, 'users': users})

@app.route('/api/admin/users/<username>', methods=['DELETE'])
def api_delete_user(username):
    """删除用户（管理员）"""
    if 'user' not in session:
        return jsonify({'success': False, 'message': '请先登录'})
    
    user_info = auth.get_user_info(session['user'])
    if not user_info or user_info['role'] != 'admin':
        return jsonify({'success': False, 'message': '权限不足'})
    
    if username == session['user']:
        return jsonify({'success': False, 'message': '不能删除当前登录的管理员'})
    
    result = auth.delete_user(username)
    return jsonify(result)

@app.route('/api/admin/stats', methods=['GET'])
def api_get_stats():
    """获取统计信息（管理员）"""
    if 'user' not in session:
        return jsonify({'success': False, 'message': '请先登录'})
    
    user_info = auth.get_user_info(session['user'])
    if not user_info or user_info['role'] != 'admin':
        return jsonify({'success': False, 'message': '权限不足'})
    
    stats = auth.get_stats()
    return jsonify({'success': True, 'stats': stats})

@app.route('/api/user/info')
def api_user_info():
    """获取当前用户信息"""
    if 'user' not in session:
        return jsonify({'success': False, 'message': '未登录'})
    
    user_info = auth.get_user_info(session['user'])
    if user_info:
        return jsonify({'success': True, 'user': user_info})
    return jsonify({'success': False, 'message': '用户不存在'})

# ==================== 预加载知识库 ====================

def load_knowledge_base():
    knowledge_dir = 'preload_knowledge'
    if os.path.exists(knowledge_dir):
        for filename in os.listdir(knowledge_dir):
            if filename.endswith('.md'):
                filepath = os.path.join(knowledge_dir, filename)
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read()
                rag_engine.add_document(filename, content)
        print("知识库预加载完成")
    else:
        print(f"预加载目录不存在: {knowledge_dir}")

if __name__ == '__main__':
    load_knowledge_base()
    
    # 在 Render 上运行时，使用环境变量 PORT
    port = int(os.environ.get('PORT', 5000))
    
    print("="*50)
    print("化工AI专业版系统启动中...")
    print(f"访问地址: http://localhost:{port}")
    print("="*50)
    app.run(host='0.0.0.0', port=port, debug=False)