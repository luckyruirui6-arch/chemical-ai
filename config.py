import os

class Config:
    # 基础配置
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'chemical-ai-secret-key-2024'
    
    # 阿里云API配置 - 从环境变量读取
    DASHSCOPE_API_KEY = os.environ.get('DASHSCOPE_API_KEY')
    
    # 如果环境变量没有设置，给出友好提示
    if not DASHSCOPE_API_KEY:
        print("⚠️ 警告: 请设置环境变量 DASHSCOPE_API_KEY")
    
    # 模型配置
    LLM_MODEL = 'qwen-max'
    EMBEDDING_MODEL = 'text-embedding-v2'
    
    # 数据库配置
    DATABASE_PATH = 'database/chemical_ai.db'
    
    # 知识库配置
    CHUNK_SIZE = 500
    CHUNK_OVERLAP = 50
    TOP_K_RESULTS = 5
    
    # 默认管理员账户
    DEFAULT_ADMIN = {
        'username': 'admin',
        'password': 'admin123'
    }