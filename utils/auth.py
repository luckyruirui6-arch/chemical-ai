"""
用户认证模块 - 支持数据库存储和激活码系统
"""
import sqlite3
import hashlib
import secrets
import string
from datetime import datetime
from config import Config
import os

class Auth:
    def __init__(self):
        # 确保数据库目录存在
        os.makedirs(os.path.dirname(Config.DATABASE_PATH), exist_ok=True)
        self.db_path = Config.DATABASE_PATH
        self._init_db()
    
    def _init_db(self):
        """初始化数据库表"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 用户表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                email TEXT,
                role TEXT DEFAULT 'user',
                subscription_type TEXT DEFAULT 'free',
                subscription_expire TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # 激活码表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS invite_codes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                code TEXT UNIQUE NOT NULL,
                status TEXT DEFAULT 'unused',
                price INTEGER DEFAULT 99,
                created_by TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                used_by TEXT,
                used_at TIMESTAMP
            )
        ''')
        
        # 检查是否需要插入默认管理员
        cursor.execute('SELECT COUNT(*) FROM users WHERE username = ?', ('admin',))
        if cursor.fetchone()[0] == 0:
            # 创建默认管理员
            admin_pwd = hashlib.sha256(Config.DEFAULT_ADMIN['password'].encode()).hexdigest()
            cursor.execute(
                'INSERT INTO users (username, password, role, subscription_type) VALUES (?, ?, ?, ?)',
                ('admin', admin_pwd, 'admin', 'vip')
            )
        
        conn.commit()
        conn.close()
    
    def _hash_password(self, password):
        """密码加密"""
        return hashlib.sha256(password.encode()).hexdigest()
    
    def verify_user(self, username, password):
        """验证用户名密码"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        hashed = self._hash_password(password)
        cursor.execute(
            'SELECT username, role FROM users WHERE username = ? AND password = ?',
            (username, hashed)
        )
        result = cursor.fetchone()
        conn.close()
        
        if result:
            return {'username': result[0], 'role': result[1]}
        return False
    
    def register_user(self, username, password, email='', invite_code=None):
        """注册新用户（需要激活码）"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # 验证激活码
            if not invite_code:
                return {'success': False, 'message': '请填写激活码'}
            
            cursor.execute('SELECT id, status FROM invite_codes WHERE code = ?', (invite_code,))
            code_data = cursor.fetchone()
            
            if not code_data:
                return {'success': False, 'message': '激活码无效'}
            
            if code_data[1] != 'unused':
                return {'success': False, 'message': '激活码已被使用'}
            
            # 注册用户
            hashed = self._hash_password(password)
            cursor.execute(
                'INSERT INTO users (username, password, email, subscription_type) VALUES (?, ?, ?, ?)',
                (username, hashed, email, 'vip')
            )
            
            # 更新激活码状态
            cursor.execute(
                'UPDATE invite_codes SET status = ?, used_by = ?, used_at = ? WHERE id = ?',
                ('used', username, datetime.now().isoformat(), code_data[0])
            )
            
            conn.commit()
            return {'success': True, 'message': '注册成功'}
            
        except sqlite3.IntegrityError:
            return {'success': False, 'message': '用户名已存在'}
        except Exception as e:
            return {'success': False, 'message': str(e)}
        finally:
            conn.close()
    
    def generate_invite_codes(self, count, created_by):
        """生成激活码"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        codes = []
        for _ in range(count):
            code = self._generate_unique_code()
            cursor.execute(
                'INSERT INTO invite_codes (code, created_by, price) VALUES (?, ?, ?)',
                (code, created_by, 99)
            )
            codes.append(code)
        
        conn.commit()
        conn.close()
        return codes
    
    def _generate_unique_code(self):
        """生成唯一激活码"""
        alphabet = string.ascii_uppercase + string.digits
        while True:
            code = ''.join(secrets.choice(alphabet) for _ in range(16))
            # 格式化：XXXX-XXXX-XXXX-XXXX
            formatted = '-'.join([code[i:i+4] for i in range(0, 16, 4)])
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('SELECT COUNT(*) FROM invite_codes WHERE code = ?', (formatted,))
            exists = cursor.fetchone()[0]
            conn.close()
            
            if not exists:
                return formatted
    
    def get_invite_codes(self, status=None):
        """获取激活码列表"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        if status:
            cursor.execute(
                'SELECT id, code, status, price, created_by, created_at, used_by, used_at FROM invite_codes WHERE status = ? ORDER BY id DESC',
                (status,)
            )
        else:
            cursor.execute('SELECT id, code, status, price, created_by, created_at, used_by, used_at FROM invite_codes ORDER BY id DESC')
        
        codes = cursor.fetchall()
        conn.close()
        
        return [
            {
                'id': c[0],
                'code': c[1],
                'status': c[2],
                'price': c[3],
                'created_by': c[4],
                'created_at': c[5],
                'used_by': c[6],
                'used_at': c[7]
            }
            for c in codes
        ]
    
    def delete_invite_code(self, code_id):
        """删除激活码"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('DELETE FROM invite_codes WHERE id = ?', (code_id,))
        conn.commit()
        affected = cursor.rowcount
        conn.close()
        return affected > 0
    
    def get_user_info(self, username):
        """获取用户信息"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(
            'SELECT username, email, role, subscription_type, subscription_expire, created_at FROM users WHERE username = ?',
            (username,)
        )
        result = cursor.fetchone()
        conn.close()
        
        if result:
            return {
                'username': result[0],
                'email': result[1],
                'role': result[2],
                'subscription_type': result[3],
                'subscription_expire': result[4],
                'created_at': result[5]
            }
        return None
    
    def list_users(self):
        """列出所有用户（管理员功能）"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('SELECT id, username, email, role, subscription_type, created_at FROM users')
        users = cursor.fetchall()
        conn.close()
        
        return [
            {
                'id': u[0],
                'username': u[1],
                'email': u[2],
                'role': u[3],
                'subscription_type': u[4],
                'created_at': u[5]
            }
            for u in users
        ]
    
    def delete_user(self, username):
        """删除用户（管理员功能）"""
        if username == 'admin':
            return {'success': False, 'message': '不能删除管理员账户'}
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('DELETE FROM users WHERE username = ?', (username,))
        conn.commit()
        affected = cursor.rowcount
        conn.close()
        
        if affected > 0:
            return {'success': True, 'message': '删除成功'}
        return {'success': False, 'message': '用户不存在'}
    
    def get_stats(self):
        """获取统计信息"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT COUNT(*) FROM users WHERE role = "user"')
        total_users = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM invite_codes WHERE status = "unused"')
        unused_codes = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM invite_codes WHERE status = "used"')
        used_codes = cursor.fetchone()[0]
        
        conn.close()
        
        return {
            'total_users': total_users,
            'unused_codes': unused_codes,
            'used_codes': used_codes,
            'code_price': 99
        }