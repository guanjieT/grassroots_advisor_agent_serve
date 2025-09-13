"""
案例驱动解决方案系统
基于成功案例的智能解决方案生成系统
"""
import os
import json
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.embeddings import DashScopeEmbeddings
from langchain_chroma import Chroma
from src.utils.logger import logger
from config import config

class CaseDrivenSystem:
    """案例驱动解决方案系统"""
    
    def __init__(self, collection_name: str = "case_knowledge_base"):
        """
        初始化案例驱动系统
        
        Args:
            collection_name: 向量数据库集合名称
        """
        self.collection_name = collection_name
        self.persist_directory = os.path.join(config.CHROMA_PERSIST_DIRECTORY, "case_driven")
        
        # 初始化嵌入模型
        self.embeddings = DashScopeEmbeddings(
            model=config.EMBEDDING_MODEL,
            dashscope_api_key=config.DASHSCOPE_API_KEY
        )
        
        # 初始化文本分割器
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=config.CHUNK_SIZE,
            chunk_overlap=config.CHUNK_OVERLAP,
            separators=["\n\n", "\n", "。", "；", "，", " ", ""]
        )
        
        # 初始化向量存储
        self.vectorstore = None
        self.retriever = None
        
        # 确保持久化目录存在
        os.makedirs(self.persist_directory, exist_ok=True)
        
        logger.info(f"案例驱动系统初始化完成，集合名称: {collection_name}")
    
    def initialize_vectorstore(self) -> bool:
        """初始化向量存储"""
        try:
            self.vectorstore = Chroma(
                collection_name=self.collection_name,
                embedding_function=self.embeddings,
                persist_directory=self.persist_directory
            )
            
            self.retriever = self.vectorstore.as_retriever(
                search_type="similarity",
                search_kwargs={"k": config.RETRIEVAL_K}
            )
            
            logger.info("案例向量存储初始化成功")
            return True
            
        except Exception as e:
            logger.error(f"案例向量存储初始化失败: {e}")
            return False
    
    def add_cases(self, cases: List[Document]) -> bool:
        """
        添加案例到向量存储
        
        Args:
            cases: 案例文档列表
            
        Returns:
            是否成功
        """
        try:
            if not self.vectorstore:
                if not self.initialize_vectorstore():
                    return False
            
            # 分割长案例
            split_cases = []
            for case in cases:
                if len(case.page_content) > config.CHUNK_SIZE:
                    chunks = self.text_splitter.split_documents([case])
                    split_cases.extend(chunks)
                else:
                    split_cases.append(case)
            
            # 添加到向量存储
            self.vectorstore.add_documents(split_cases)
            
            logger.info(f"成功添加 {len(split_cases)} 个案例片段")
            return True
            
        except Exception as e:
            logger.error(f"添加案例失败: {e}")
            return False
    
    def find_similar_cases(
        self, 
        problem_description: str, 
        k: int = 5,
        category_filter: Optional[str] = None
    ) -> List[Document]:
        """
        查找相似案例
        
        Args:
            problem_description: 问题描述
            k: 返回结果数量
            category_filter: 类别过滤
            
        Returns:
            相似案例列表
        """
        try:
            if not self.vectorstore:
                if not self.initialize_vectorstore():
                    return []
            
            # 构建过滤条件
            filter_dict = None
            if category_filter:
                filter_dict = {"category": category_filter}
            
            # 执行相似性搜索
            if filter_dict:
                results = self.vectorstore.similarity_search(
                    query=problem_description,
                    k=k,
                    filter=filter_dict
                )
            else:
                results = self.vectorstore.similarity_search(
                    query=problem_description,
                    k=k
                )
            
            logger.info(f"找到 {len(results)} 个相似案例")
            return results
            
        except Exception as e:
            logger.error(f"查找相似案例失败: {e}")
            return []
    
    def get_case_statistics(self) -> Dict[str, Any]:
        """获取案例统计信息"""
        try:
            if not self.vectorstore:
                if not self.initialize_vectorstore():
                    return {"error": "向量存储初始化失败"}
            
            # 获取文档数量
            collection = self.vectorstore._collection
            count = collection.count()
            
            # 获取一些示例案例
            sample_cases = self.vectorstore.similarity_search("", k=5)
            
            # 统计类别分布
            categories = {}
            for case in sample_cases:
                category = case.metadata.get("category", "未分类")
                categories[category] = categories.get(category, 0) + 1
            
            stats = {
                "total_cases": count,
                "categories": categories,
                "sample_cases": [
                    {
                        "title": case.metadata.get("title", "未知"),
                        "category": case.metadata.get("category", "未知"),
                        "content_preview": case.page_content[:100] + "..."
                    }
                    for case in sample_cases
                ]
            }
            
            return stats
            
        except Exception as e:
            logger.error(f"获取案例统计失败: {e}")
            return {"error": str(e)}