"""
向量数据库管理器
使用ChromaDB进行向量存储和检索
"""
import os
from tqdm import tqdm
from typing import List, Optional, Dict, Any
from langchain_core.documents import Document
from langchain_openai import OpenAIEmbeddings
from langchain_community.embeddings import DashScopeEmbeddings
from langchain_chroma import Chroma
from langchain_core.vectorstores import VectorStoreRetriever
from src.utils.logger import logger
from config import config

class VectorStoreManager:
    """向量数据库管理器"""
    
    def __init__(self, collection_name: str = "grassroots_cases"):
        """
        初始化向量数据库管理器
        
        Args:
            collection_name: 集合名称
        """
        self.collection_name = collection_name
        self.persist_directory = config.CHROMA_PERSIST_DIRECTORY
        
        # 初始化嵌入模型
        self.embeddings = DashScopeEmbeddings(
            dashscope_api_key=config.DASHSCOPE_API_KEY,
            model=config.EMBEDDING_MODEL
        )
        
        # 初始化向量数据库
        self.vectorstore = None
        self._initialize_vectorstore()
    
    def _initialize_vectorstore(self):
        """初始化向量数据库"""
        try:
            # 确保持久化目录存在
            os.makedirs(self.persist_directory, exist_ok=True)
            
            # 初始化ChromaDB
            self.vectorstore = Chroma(
                collection_name=self.collection_name,
                embedding_function=self.embeddings,
                persist_directory=self.persist_directory
            )
            
            logger.info(f"向量数据库初始化成功: {self.collection_name}")
            
        except Exception as e:
            logger.error(f"向量数据库初始化失败: {e}")
            raise
    
    def add_documents(self, documents: List[Document]) -> bool:
        """
        添加文档到向量数据库
        
        Args:
            documents: 文档列表
            
        Returns:
            是否添加成功
        """
        try:
            if not documents:
                logger.warning("没有文档需要添加")
                return False
            
            # 添加文档
            # self.vectorstore.add_documents(documents)
            batch_size = 100
            logger.info(f"开始向向量数据库添加 {len(documents)} 个文档，批次大小为 {batch_size}...")
            for i in tqdm(range(0, len(documents), batch_size), desc="添加文档到向量库"):
                batch = documents[i:i + batch_size]
                self.vectorstore.add_documents(batch)
            
            logger.info(f"成功添加 {len(documents)} 个文档到向量数据库")
            return True
            
        except Exception as e:
            logger.error(f"添加文档失败: {e}")
            return False
    
    def get_retriever(
        self, 
        search_type: str = "similarity_score_threshold",
        search_kwargs: Optional[Dict[str, Any]] = None
    ) -> VectorStoreRetriever:
        """
        获取检索器
        
        Args:
            search_type: 搜索类型 ("similarity", "similarity_score_threshold", "mmr")
            search_kwargs: 搜索参数
            
        Returns:
            检索器实例
        """
        try:
            # 默认搜索参数
            default_kwargs = {
                "k": config.RETRIEVAL_K,
                "score_threshold": config.SCORE_THRESHOLD
            }
            
            if search_kwargs:
                default_kwargs.update(search_kwargs)
            
            retriever = self.vectorstore.as_retriever(
                search_type=search_type,
                search_kwargs=default_kwargs
            )
            
            logger.info(f"检索器创建成功: {search_type}")
            return retriever
            
        except Exception as e:
            logger.error(f"创建检索器失败: {e}")
            raise
    
    def search_similar_documents(
        self, 
        query: str, 
        k: int = None,
        score_threshold: float = None
    ) -> List[Document]:
        """
        搜索相似文档
        
        Args:
            query: 查询文本
            k: 返回文档数量
            score_threshold: 相似度阈值
            
        Returns:
            相似文档列表
        """
        try:
            k = k or config.RETRIEVAL_K
            score_threshold = score_threshold or config.SCORE_THRESHOLD
            
            # 优先使用相关性分数（越大越相关），失败则回退到距离分数
            filtered_docs: List[Document] = []
            try:
                docs_with_scores = self.vectorstore.similarity_search_with_relevance_scores(
                    query,
                    k=k
                )
                filtered_docs = [doc for doc, relevance in docs_with_scores if float(relevance) >= (score_threshold or 0.0)]
            except Exception:
                # 距离分数（越小越相似），阈值解释改为最大允许距离
                distance_threshold = score_threshold if score_threshold is not None else 0.6
                docs_with_scores = self.vectorstore.similarity_search_with_score(
                    query,
                    k=k
                )
                filtered_docs = [doc for doc, distance in docs_with_scores if float(distance) <= distance_threshold]
            
            logger.info(f"搜索到 {len(filtered_docs)} 个相关文档 (阈值: {score_threshold})")
            return filtered_docs
            
        except Exception as e:
            logger.error(f"搜索文档失败: {e}")
            return []
    
    def get_collection_info(self) -> Dict[str, Any]:
        """
        获取集合信息
        
        Returns:
            集合信息字典
        """
        try:
            # 获取集合
            collection = self.vectorstore._collection
            
            info = {
                "collection_name": self.collection_name,
                "document_count": collection.count(),
                "persist_directory": self.persist_directory
            }
            
            return info
            
        except Exception as e:
            logger.error(f"获取集合信息失败: {e}")
            return {}
    
    def delete_collection(self) -> bool:
        """
        删除集合
        
        Returns:
            是否删除成功
        """
        try:
            # 删除集合
            self.vectorstore.delete_collection()
            
            # 重新初始化
            self._initialize_vectorstore()
            
            logger.info(f"集合 {self.collection_name} 已删除并重新创建")
            return True
            
        except Exception as e:
            logger.error(f"删除集合失败: {e}")
            return False
    
    def update_documents(self, documents: List[Document]) -> bool:
        """
        更新文档（删除旧的，添加新的）
        
        Args:
            documents: 新文档列表
            
        Returns:
            是否更新成功
        """
        try:
            # 删除现有集合
            if not self.delete_collection():
                return False
            
            # 添加新文档
            return self.add_documents(documents)
            
        except Exception as e:
            logger.error(f"更新文档失败: {e}")
            return False

def build_knowledge_base(include_rules: bool = True):
    """
    构建知识库的便捷函数
    
    Args:
        include_rules: 是否包含法规政策数据
    """
    from src.knowledge_base.loader import CaseLoader, create_sample_cases
    from src.knowledge_base.rules_processor import RulesProcessor
    
    try:
        all_documents = []
        
        # 1. 加载案例数据
        # 创建示例案例（如果不存在）
        sample_path = "./data/knowledge_base/sample_cases.json"
        if not os.path.exists(sample_path):
            create_sample_cases(sample_path)
        
        # 加载案例
        loader = CaseLoader()
        case_documents = loader.load_from_directory("./data/knowledge_base")
        
        if case_documents:
            # 分割文档
            split_case_docs = loader.split_documents(case_documents)
            all_documents.extend(split_case_docs)
            logger.info(f"加载案例文档: {len(split_case_docs)} 个")
        
        # 2. 加载法规政策数据（如果启用）
        if include_rules:
            try:
                rules_processor = RulesProcessor()
                rules_documents = rules_processor.create_rules_knowledge_base()
                
                if rules_documents:
                    all_documents.extend(rules_documents)
                    logger.info(f"加载法规政策文档: {len(rules_documents)} 个")
                else:
                    logger.warning("未能加载法规政策文档")
            except Exception as e:
                logger.error(f"处理法规政策文档失败: {e}")
                logger.info("继续使用案例数据构建知识库...")
        
        if not all_documents:
            logger.error("没有找到任何文档")
            return False
        
        # 3. 创建向量数据库管理器
        vector_manager = VectorStoreManager()
        
        # 4. 添加文档到向量数据库
        success = vector_manager.add_documents(all_documents)
        
        if success:
            # 获取集合信息
            info = vector_manager.get_collection_info()
            logger.info(f"知识库构建完成: {info}")
            logger.info(f"总文档数: {len(all_documents)} (案例: {len(all_documents) - (len(rules_documents) if include_rules and 'rules_documents' in locals() else 0)}, 法规: {len(rules_documents) if include_rules and 'rules_documents' in locals() else 0})")
            return True
        else:
            logger.error("知识库构建失败")
            return False
            
    except Exception as e:
        logger.error(f"构建知识库时出错: {e}")
        return False

if __name__ == "__main__":
    # 构建知识库
    success = build_knowledge_base()
    
    if success:
        # 测试检索
        vector_manager = VectorStoreManager()
        
        # 测试搜索
        test_query = "如何解决邻里纠纷？"
        docs = vector_manager.search_similar_documents(test_query, k=3)
        
        print(f"\n搜索查询: {test_query}")
        print(f"找到 {len(docs)} 个相关文档:")
        
        for i, doc in enumerate(docs, 1):
            print(f"\n文档 {i}:")
            print(f"标题: {doc.metadata.get('title', '未知')}")
            print(f"类别: {doc.metadata.get('category', '未知')}")
            print(f"内容预览: {doc.page_content[:200]}...")
    else:
        print("知识库构建失败") 