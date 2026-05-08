"""
数据模型定义
"""
import sqlite3
import os
from config import Config

class Database:
    def __init__(self):
        os.makedirs(os.path.dirname(Config.DATABASE_PATH), exist_ok=True)
        self.conn = sqlite3.connect(Config.DATABASE_PATH)
        self._create_tables()
    
    def _create_tables(self):
        cursor = self.conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS documents (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                filename TEXT NOT NULL,
                content TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS chat_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user TEXT NOT NULL,
                question TEXT NOT NULL,
                answer TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        self.conn.commit()
    
    def add_document(self, filename, content):
        cursor = self.conn.cursor()
        cursor.execute(
            'INSERT INTO documents (filename, content) VALUES (?, ?)',
            (filename, content)
        )
        self.conn.commit()
        return cursor.lastrowid
    
    def get_all_documents(self):
        cursor = self.conn.cursor()
        cursor.execute('SELECT id, filename, content FROM documents')
        return cursor.fetchall()
