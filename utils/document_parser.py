"""
文档解析模块
支持 .md, .txt, .pdf, .docx 等格式
"""
import os
from PyPDF2 import PdfReader
from docx import Document

class DocumentParser:
    def parse_file(self, file):
        """解析上传的文件"""
        filename = file.filename.lower()
        
        if filename.endswith('.pdf'):
            return self._parse_pdf(file)
        elif filename.endswith('.docx'):
            return self._parse_docx(file)
        elif filename.endswith('.md') or filename.endswith('.txt'):
            return file.read().decode('utf-8')
        else:
            raise ValueError(f"不支持的文件格式: {filename}")
    
    def _parse_pdf(self, file):
        """解析PDF文件"""
        reader = PdfReader(file)
        text = ""
        for page in reader.pages:
            text += page.extract_text() + "\n"
        return text
    
    def _parse_docx(self, file):
        """解析Word文档"""
        doc = Document(file)
        text = ""
        for para in doc.paragraphs:
            text += para.text + "\n"
        return text
