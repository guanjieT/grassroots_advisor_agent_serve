"""
政策RAG系统
专门针对政策法规数据的检索增强生成系统
"""
import os
import json
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.embeddings import DashScopeEmbeddings
from langchain_chroma import Chroma
from langchain_core.vectorstores import VectorStoreRetriever
from src.utils.logger import logger
from config import config

class PolicyRAGSystem:
    """政策RAG系统"""
    
    def __init__(self, collection_name: str = "policy_knowledge_base"):
        """
        初始化政策RAG系统
        
        Args:
            collection_name: 向量数据库集合名称
        """
        self.collection_name = collection_name
        self.persist_directory = os.path.join(config.CHROMA_PERSIST_DIRECTORY, "policy_rag")
        
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
        
        logger.info(f"政策RAG系统初始化完成，集合名称: {collection_name}")
    
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
            
            logger.info("向量存储初始化成功")
            return True
            
        except Exception as e:
            logger.error(f"向量存储初始化失败: {e}")
            return False
    
    def add_documents(self, documents: List[Document]) -> bool:
        """
        添加文档到向量存储
        
        Args:
            documents: 文档列表
            
        Returns:
            是否成功
        """
        try:
            if not self.vectorstore:
                if not self.initialize_vectorstore():
                    return False
            
            # 分割长文档
            split_documents = []
            for doc in documents:
                if len(doc.page_content) > config.CHUNK_SIZE:
                    chunks = self.text_splitter.split_documents([doc])
                    split_documents.extend(chunks)
                else:
                    split_documents.append(doc)
            
            # 添加到向量存储
            self.vectorstore.add_documents(split_documents)
            
            logger.info(f"成功添加 {len(split_documents)} 个文档片段")
            return True
            
        except Exception as e:
            logger.error(f"添加文档失败: {e}")
            return False
    
    def search_policies(
        self, 
        query: str, 
        k: int = 5,
        filter_dict: Optional[Dict[str, Any]] = None
    ) -> List[Document]:
        """
        搜索相关政策
        
        Args:
            query: 查询文本
            k: 返回结果数量
            filter_dict: 过滤条件
            
        Returns:
            相关文档列表
        """
        try:
            if not self.vectorstore:
                if not self.initialize_vectorstore():
                    return []
            
            # 执行相似性搜索
            if filter_dict:
                results = self.vectorstore.similarity_search(
                    query=query,
                    k=k,
                    filter=filter_dict
                )
            else:
                results = self.vectorstore.similarity_search(
                    query=query,
                    k=k
                )
            
            logger.info(f"搜索到 {len(results)} 个相关政策")
            return results
            
        except Exception as e:
            logger.error(f"搜索政策失败: {e}")
            return []
    
    def search_with_scores(
        self, 
        query: str, 
        k: int = 5,
        score_threshold: float = 0.5
    ) -> List[Tuple[Document, float]]:
        """
        带相似度分数的搜索
        
        Args:
            query: 查询文本
            k: 返回结果数量
            score_threshold: 相似度阈值
            
        Returns:
            (文档, 相似度分数) 元组列表
        """
        try:
            if not self.vectorstore:
                if not self.initialize_vectorstore():
                    return []
            
            results = self.vectorstore.similarity_search_with_score(
                query=query,
                k=k
            )
            
            # 过滤低分结果
            filtered_results = [
                (doc, score) for doc, score in results 
                if score >= score_threshold
            ]
            
            logger.info(f"搜索到 {len(filtered_results)} 个高质量匹配结果")
            return filtered_results
            
        except Exception as e:
            logger.error(f"带分数搜索失败: {e}")
            return []
    
    def get_collection_info(self) -> Dict[str, Any]:
        """获取集合信息"""
        try:
            if not self.vectorstore:
                if not self.initialize_vectorstore():
                    return {"error": "向量存储初始化失败"}
            
            # 获取文档数量
            collection = self.vectorstore._collection
            count = collection.count()
            
            # 获取一些示例文档
            sample_docs = self.vectorstore.similarity_search("", k=3)
            
            info = {
                "collection_name": self.collection_name,
                "document_count": count,
                "persist_directory": self.persist_directory,
                "sample_documents": [
                    {
                        "title": doc.metadata.get("title", "未知"),
                        "source": doc.metadata.get("source", "未知"),
                        "content_preview": doc.page_content[:100] + "..."
                    }
                    for doc in sample_docs
                ]
            }
            
            return info
            
        except Exception as e:
            logger.error(f"获取集合信息失败: {e}")
            return {"error": str(e)}
    
    def delete_collection(self) -> bool:
        """删除集合"""
        try:
            if self.vectorstore:
                self.vectorstore.delete_collection()
                self.vectorstore = None
                self.retriever = None
            
            logger.info(f"集合 {self.collection_name} 已删除")
            return True
            
        except Exception as e:
            logger.error(f"删除集合失败: {e}")
            return False
    
    def export_documents(self, output_path: str) -> bool:
        """导出文档数据"""
        try:
            if not self.vectorstore:
                if not self.initialize_vectorstore():
                    return False
            
            # 获取所有文档
            all_docs = self.vectorstore.similarity_search("", k=10000)
            
            # 转换为可序列化格式
            export_data = []
            for doc in all_docs:
                export_data.append({
                    "content": doc.page_content,
                    "metadata": doc.metadata
                })
            
            # 保存到文件
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, ensure_ascii=False, indent=2)
            
            logger.info(f"成功导出 {len(export_data)} 个文档到 {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"导出文档失败: {e}")
            return False