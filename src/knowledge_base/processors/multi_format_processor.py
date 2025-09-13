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
from src.utils.logger import logger
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
    
    def _process_json(self, file_path: str) -> List[Document]:
        """处理JSON文件"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            documents = []
            
            if isinstance(data, list):
                for item in data:
                    doc = self._create_document_from_dict(item, file_path)
                    if doc:
                        documents.append(doc)
            elif isinstance(data, dict):
                doc = self._create_document_from_dict(data, file_path)
                if doc:
                    documents.append(doc)
            
            return documents
            
        except Exception as e:
            logger.error(f"处理JSON文件失败 {file_path}: {e}")
            return []
    
    def _process_excel(self, file_path: str) -> List[Document]:
        """处理Excel文件"""
        try:
            df = pd.read_excel(file_path)
            documents = []
            
            for _, row in df.iterrows():
                doc = self._create_document_from_dict(row.to_dict(), file_path)
                if doc:
                    documents.append(doc)
            
            return documents
            
        except Exception as e:
            logger.error(f"处理Excel文件失败 {file_path}: {e}")
            return []
    
    def _process_csv(self, file_path: str) -> List[Document]:
        """处理CSV文件"""
        try:
            df = pd.read_csv(file_path, encoding='utf-8')
            documents = []
            
            for _, row in df.iterrows():
                doc = self._create_document_from_dict(row.to_dict(), file_path)
                if doc:
                    documents.append(doc)
            
            return documents
            
        except Exception as e:
            logger.error(f"处理CSV文件失败 {file_path}: {e}")
            return []
    
    def _process_xml(self, file_path: str) -> List[Document]:
        """处理XML文件"""
        try:
            tree = ET.parse(file_path)
            root = tree.getroot()
            
            documents = []
            
            # 如果根元素包含多个子元素，每个子元素作为一个文档
            if len(root) > 1:
                for child in root:
                    doc_data = self._xml_to_dict(child)
                    doc = self._create_document_from_dict(doc_data, file_path)
                    if doc:
                        documents.append(doc)
            else:
                # 整个XML作为一个文档
                doc_data = self._xml_to_dict(root)
                doc = self._create_document_from_dict(doc_data, file_path)
                if doc:
                    documents.append(doc)
            
            return documents
            
        except Exception as e:
            logger.error(f"处理XML文件失败 {file_path}: {e}")
            return []
    
    def _process_text(self, file_path: str) -> List[Document]:
        """处理文本文件"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            if not content.strip():
                return []
            
            # 分割长文本
            chunks = self.text_splitter.split_text(content)
            
            documents = []
            for i, chunk in enumerate(chunks):
                metadata = {
                    'source': file_path,
                    'filename': Path(file_path).name,
                    'chunk_index': i,
                    'total_chunks': len(chunks),
                    'file_type': Path(file_path).suffix
                }
                
                documents.append(Document(
                    page_content=chunk,
                    metadata=metadata
                ))
            
            return documents
            
        except Exception as e:
            logger.error(f"处理文本文件失败 {file_path}: {e}")
            return []
    
    def _xml_to_dict(self, element) -> Dict[str, Any]:
        """将XML元素转换为字典"""
        result = {}
        
        # 添加元素文本
        if element.text and element.text.strip():
            result['text'] = element.text.strip()
        
        # 添加属性
        if element.attrib:
            result.update(element.attrib)
        
        # 添加子元素
        for child in element:
            child_data = self._xml_to_dict(child)
            if child.tag in result:
                if not isinstance(result[child.tag], list):
                    result[child.tag] = [result[child.tag]]
                result[child.tag].append(child_data)
            else:
                result[child.tag] = child_data
        
        return result
    
    def _create_document_from_dict(self, data: Dict[str, Any], source_path: str) -> Optional[Document]:
        """从字典创建文档对象"""
        try:
            # 标准化字段名
            normalized_data = self._normalize_fields(data)
            
            # 构建文档内容
            content_parts = []
            
            # 标题
            title = normalized_data.get('title', '')
            if title:
                content_parts.append(f"标题: {title}")
            
            # 主要内容
            content = normalized_data.get('content', '')
            if content:
                content_parts.append(f"内容: {content}")
            
            # 摘要
            summary = normalized_data.get('summary', '')
            if summary:
                content_parts.append(f"摘要: {summary}")
            
            # 如果没有主要内容，使用所有非空字段
            if not content_parts:
                for key, value in normalized_data.items():
                    if value and str(value).strip():
                        content_parts.append(f"{key}: {value}")
            
            if not content_parts:
                return None
            
            # 构建元数据
            metadata = {
                'source': source_path,
                'filename': Path(source_path).name,
                'title': title or Path(source_path).stem,
                'authority': normalized_data.get('authority', ''),
                'publish_date': normalized_data.get('publish_date', ''),
                'category': normalized_data.get('category', ''),
                'level': normalized_data.get('level', ''),
                'keywords': normalized_data.get('keywords', ''),
                'file_type': Path(source_path).suffix
            }
            
            # 清理元数据中的空值
            metadata = {k: v for k, v in metadata.items() if v}
            
            document_content = '\n\n'.join(content_parts)
            
            return Document(
                page_content=document_content,
                metadata=metadata
            )
            
        except Exception as e:
            logger.error(f"创建文档失败: {e}")
            return None
    
    def _normalize_fields(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """标准化字段名"""
        normalized = {}
        
        for standard_field, possible_names in self.field_mapping.items():
            for possible_name in possible_names:
                if possible_name in data and data[possible_name]:
                    normalized[standard_field] = data[possible_name]
                    break
        
        return normalized