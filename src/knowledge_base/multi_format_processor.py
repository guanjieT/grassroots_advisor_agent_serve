"""
多格式政策法规数据处理器
支持处理各种格式的政策法规文件
"""
import os
import json
import xml.etree.ElementTree as ET
from typing import List, Dict, Any, Optional, Union
from pathlib import Path
import pandas as pd
from langchain_core.documents import Document
from langchain.text_splitter import RecursiveCharacterTextSplitter
from utils.logger import logger
from config import config

class MultiFormatProcessor:
    """多格式政策法规处理器"""
    
    def __init__(self):
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=config.CHUNK_SIZE,
            chunk_overlap=config.CHUNK_OVERLAP,
            separators=["\n\n", "\n", "。", "；", "，", " ", ""]
        )
        
        # 支持的文件格式
        self.supported_formats = {
            '.json': self._process_json,
            '.xlsx': self._process_excel,
            '.xls': self._process_excel,
            '.csv': self._process_csv,
            '.xml': self._process_xml,
            '.txt': self._process_text,
            '.md': self._process_text
        }
        
        # 政策法规字段映射
        self.field_mapping = {
            # 标准字段名 -> 可能的字段名列表
            'title': ['标题', '名称', '法规名称', '政策名称', 'title', 'name'],
            'content': ['内容', '正文', '条文', '全文', '主要内容', 'content', 'text'],
            'authority': ['发布机关', '制定机关', '发文机关', '颁布机关', 'authority', 'issuer'],
            'publish_date': ['发布日期', '颁布日期', '生效日期', 'publish_date', 'date'],
            'category': ['类别', '分类', '领域', 'category', 'type'],
            'level': ['效力级别', '层级', '级别', 'level'],
            'keywords': ['关键词', '标签', 'keywords', 'tags'],
            'summary': ['摘要', '概述', '简介', 'summary', 'abstract']
        }
    
    def process_file(self, file_path: str) -> List[Document]:
        """
        处理单个文件
        
        Args:
            file_path: 文件路径
            
        Returns:
            处理后的文档列表
        """
        try:
            file_ext = Path(file_path).suffix.lower()
            
            if file_ext not in self.supported_formats:
                logger.warning(f"不支持的文件格式: {file_ext}")
                return []
            
            processor = self.supported_formats[file_ext]
            documents = processor(file_path)
            
            logger.info(f"处理文件 {file_path}: {len(documents)} 个文档")
            return documents
            
        except Exception as e:
            logger.error(f"处理文件失败 {file_path}: {e}")
            return []
    
    def process_directory(self, directory_path: str) -> List[Document]:
        """
        批量处理目录中的所有文件
        
        Args:
            directory_path: 目录路径
            
        Returns:
            所有处理后的文档列表
        """
        all_documents = []
        
        if not os.path.exists(directory_path):
            logger.warning(f"目录不存在: {directory_path}")
            return []
        
        for root, dirs, files in os.walk(directory_path):
            for file in files:
                file_path = os.path.join(root, file)
                documents = self.process_file(file_path)
                all_documents.extend(documents)
        
        logger.info(f"批量处理完成: {len(all_documents)} 个文档")
        return all_documents