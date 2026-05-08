"""
RAG检索增强生成引擎
"""
import dashscope
from dashscope import TextEmbedding, Generation
from config import Config
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
import jieba
import re

class RAGEngine:
    def __init__(self):
        dashscope.api_key = Config.DASHSCOPE_API_KEY
        self.documents = []
        self.chunks = []
        self.embeddings = None
    
    def split_text(self, text, chunk_size=Config.CHUNK_SIZE, overlap=Config.CHUNK_OVERLAP):
        """文本分块"""
        sentences = re.split(r'[。！？；\n]', text)
        chunks = []
        current_chunk = ""
        
        for sentence in sentences:
            if len(current_chunk) + len(sentence) < chunk_size:
                current_chunk += sentence + "。"
            else:
                if current_chunk:
                    chunks.append(current_chunk)
                # 重叠部分
                current_chunk = current_chunk[-overlap:] if len(current_chunk) > overlap else ""
                current_chunk += sentence + "。"
        
        if current_chunk:
            chunks.append(current_chunk)
        
        return chunks
    
    def get_embedding(self, text):
        """获取文本向量"""
        response = TextEmbedding.call(
            model=Config.EMBEDDING_MODEL,
            input=text
        )
        if response.status_code == 200:
            return np.array(response.output['embeddings'][0]['embedding'])
        else:
            raise Exception(f"Embedding error: {response.message}")
    
    def add_document(self, filename, content):
        """添加文档到知识库"""
        self.documents.append({
            'filename': filename,
            'content': content
        })
        
        # 分块并向量化
        chunks = self.split_text(content)
        for chunk in chunks:
            self.chunks.append({
                'text': chunk,
                'source': filename
            })
        
        # 重新计算所有embedding
        self._compute_embeddings()
    
    def _compute_embeddings(self):
        """计算所有文本块的向量"""
        if not self.chunks:
            return
        
        texts = [chunk['text'] for chunk in self.chunks]
        response = TextEmbedding.call(
            model=Config.EMBEDDING_MODEL,
            input=texts
        )
        
        if response.status_code == 200:
            self.embeddings = np.array([
                emb['embedding'] for emb in response.output['embeddings']
            ])
        else:
            raise Exception(f"Embedding batch error: {response.message}")
    
    def retrieve(self, query, top_k=Config.TOP_K_RESULTS):
        """检索相关文档"""
        if not self.chunks or self.embeddings is None:
            return []
        
        query_embedding = self.get_embedding(query).reshape(1, -1)
        similarities = cosine_similarity(query_embedding, self.embeddings)[0]
        
        top_indices = np.argsort(similarities)[-top_k:][::-1]
        
        results = []
        for idx in top_indices:
            if similarities[idx] > 0.6:  # 相似度阈值
                results.append({
                    'text': self.chunks[idx]['text'],
                    'source': self.chunks[idx]['source'],
                    'score': float(similarities[idx])
                })
        
        return results
    
    def query(self, question):
        """使用RAG回答问题"""
        # 检索相关上下文
        relevant_docs = self.retrieve(question)
        
        # 构建prompt
        context = "\n\n".join([f"[来源: {doc['source']}]\n{doc['text']}" for doc in relevant_docs])
        
        if not context:
            context = "（未找到相关知识库内容，请基于通用化工知识回答）"
        
        prompt = f"""你是专业的化工AI助手。请基于以下知识库内容回答用户的问题。

知识库内容:
{context}

用户问题: {question}

回答要求:
1. 如果知识库中有相关内容，请基于知识库回答
2. 如果知识库中没有相关内容，可以基于通用化工专业知识回答
3. 回答要专业、准确、条理清晰
4. 涉及安全问题时要特别强调注意事项
"""
        
        # 调用大模型
        response = Generation.call(
            model=Config.LLM_MODEL,
            prompt=prompt,
            temperature=0.3
        )
        
        if response.status_code == 200:
            return response.output.text
        else:
            raise Exception(f"LLM error: {response.message}")
