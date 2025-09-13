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
from utils.logger import logger
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
            dashscope_api_key=config.DASHSCOPE_API_KEY,
            model=config.EMBEDDING_MODEL
        )
        
        # 文档分割器
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            length_function=len,
            separators=["\n\n", "\n", "。", "；", "，", " ", ""]
        )
        
        # 向量数据库
        self.vectorstore = None
        self._initialize_vectorstore()
        
        # 政策分类映射
        self.policy_categories = {
            '基层治理': ['社区治理', '网格化管理', '基层党建', '村务公开'],
            '民生保障': ['社会救助', '养老服务', '残疾人保障', '儿童保障'],
            '社会治理': ['平安建设', '矛盾纠纷调解', '信访工作', '志愿服务'],
            '公共服务': ['政务服务', '便民服务', '营商环境', '服务标准']
        }
        
        # 行政层级映射
        self.admin_levels = {
            '中央': '01_中央政策',
            '省级': '02_省级政策', 
            '市级': '03_市级政策',
            '区县': '04_区县政策',
            '街道社区': '05_街道社区'
        }
    
    def _initialize_vectorstore(self):
        """初始化向量数据库"""
        try:
            os.makedirs(self.persist_directory, exist_ok=True)
            
            self.vectorstore = Chroma(
                collection_name=self.collection_name,
                embedding_function=self.embeddings,
                persist_directory=self.persist_directory
            )
            
            logger.info(f"政策RAG向量数据库初始化成功: {self.collection_name}")
            
        except Exception as e:
            logger.error(f"政策RAG向量数据库初始化失败: {e}")
            raise
    
    def build_knowledge_base_from_optimized_data(self, data_dir: str = "./data/optimized") -> bool:
        """
        从优化后的政策数据构建知识库
        
        Args:
            data_dir: 优化后的数据目录
            
        Returns:
            是否构建成功
        """
        logger.info("开始从优化后的政策数据构建RAG知识库...")
        
        try:
            all_documents = []
            
            # 遍历所有政策文件
            for root, dirs, files in os.walk(data_dir):
                for file in files:
                    if file.endswith(('.txt', '.md')) and file not in ['README.md', 'INDEX.md']:
                        file_path = os.path.join(root, file)
                        
                        try:
                            # 读取文件内容
                            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                                content = f.read().strip()
                            
                            if not content or len(content) < 50:  # 跳过空文件或过短文件
                                continue
                            
                            # 提取元数据
                            metadata = self._extract_metadata_from_path(file_path, file)
                            
                            # 创建文档
                            doc = Document(
                                page_content=content,
                                metadata=metadata
                            )
                            
                            all_documents.append(doc)
                            
                        except Exception as e:
                            logger.warning(f"处理文件失败 {file_path}: {e}")
                            continue
            
            if not all_documents:
                logger.error("没有找到有效的政策文档")
                return False
            
            logger.info(f"成功加载 {len(all_documents)} 个政策文档")
            
            # 分割文档
            split_documents = self.text_splitter.split_documents(all_documents)
            logger.info(f"文档分割后共 {len(split_documents)} 个片段")
            
            # 清空现有数据库
            self._clear_collection()
            
            # 批量添加文档
            batch_size = 100
            for i in range(0, len(split_documents), batch_size):
                batch = split_documents[i:i + batch_size]
                self.vectorstore.add_documents(batch)
                logger.info(f"已添加 {i + len(batch)}/{len(split_documents)} 个文档片段")
            
            logger.info("政策RAG知识库构建完成")
            return True
            
        except Exception as e:
            logger.error(f"构建政策RAG知识库失败: {e}")
            return False
    
    def _extract_metadata_from_path(self, file_path: str, filename: str) -> Dict[str, Any]:
        """从文件路径提取元数据"""
        path_parts = file_path.split(os.sep)
        
        metadata = {
            'source': file_path,
            'filename': filename,
            'title': Path(filename).stem,
            'admin_level': '未知',
            'policy_domain': '未知',
            'year': '未知',
            'region': '未知',
            'doc_type': '政策文件'
        }
        
        # 提取行政层级
        for part in path_parts:
            if part.startswith(('01_', '02_', '03_', '04_', '05_')):
                for level, dir_name in self.admin_levels.items():
                    if part == dir_name:
                        metadata['admin_level'] = level
                        break
        
        # 提取政策领域
        for part in path_parts:
            for domain, subcategories in self.policy_categories.items():
                if part == domain or any(sub in part for sub in subcategories):
                    metadata['policy_domain'] = domain
                    break
        
        # 从文件名提取年份
        import re
        year_matches = re.findall(r'20\d{2}', filename)
        if year_matches:
            metadata['year'] = year_matches[0]
        
        # 提取地区信息
        regions = [
            '北京', '上海', '天津', '重庆', '河北', '山西', '辽宁', '吉林', '黑龙江',
            '江苏', '浙江', '安徽', '福建', '江西', '山东', '河南', '湖北', '湖南',
            '广东', '广西', '海南', '四川', '贵州', '云南', '西藏', '陕西', '甘肃',
            '青海', '宁夏', '新疆', '内蒙古'
        ]
        
        for region in regions:
            if region in filename:
                metadata['region'] = region
                break
        
        # 确定文档类型
        doc_type_keywords = {
            '法律法规': ['法', '条例', '法规'],
            '规章制度': ['规章', '制度', '规定', '办法'],
            '政策文件': ['意见', '通知', '方案', '计划'],
            '工作指南': ['指南', '手册', '流程', '标准']
        }
        
        for doc_type, keywords in doc_type_keywords.items():
            if any(keyword in filename for keyword in keywords):
                metadata['doc_type'] = doc_type
                break
        
        return metadata
    
    def _clear_collection(self):
        """清空集合"""
        try:
            self.vectorstore.delete_collection()
            self._initialize_vectorstore()
            logger.info("向量数据库集合已清空")
        except Exception as e:
            logger.warning(f"清空集合失败: {e}")
    
    def search_policies(
        self, 
        query: str, 
        k: int = 5,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Document]:
        """
        搜索相关政策
        
        Args:
            query: 查询文本
            k: 返回文档数量
            filters: 过滤条件
            
        Returns:
            相关政策文档列表
        """
        try:
            # 基础相似度搜索
            docs_with_scores = self.vectorstore.similarity_search_with_score(
                query, k=k*2  # 获取更多候选文档用于过滤
            )
            
            # 应用过滤条件
            filtered_docs = []
            for doc, score in docs_with_scores:
                if self._apply_filters(doc, filters):
                    filtered_docs.append((doc, score))
            
            # 按相似度排序并返回前k个
            filtered_docs.sort(key=lambda x: x[1], reverse=True)
            result_docs = [doc for doc, score in filtered_docs[:k]]
            
            logger.info(f"搜索查询: {query}, 找到 {len(result_docs)} 个相关政策")
            return result_docs
            
        except Exception as e:
            logger.error(f"搜索政策失败: {e}")
            return []
    
    def _apply_filters(self, doc: Document, filters: Optional[Dict[str, Any]]) -> bool:
        """应用过滤条件"""
        if not filters:
            return True
        
        metadata = doc.metadata
        
        # 检查各种过滤条件
        for key, value in filters.items():
            if key in metadata:
                if isinstance(value, list):
                    if metadata[key] not in value:
                        return False
                else:
                    if metadata[key] != value:
                        return False
        
        return True
    
    def get_policy_by_category(
        self, 
        category: str, 
        subcategory: Optional[str] = None,
        k: int = 10
    ) -> List[Document]:
        """
        按类别获取政策
        
        Args:
            category: 主要类别
            subcategory: 子类别
            k: 返回文档数量
            
        Returns:
            该类别的政策文档
        """
        filters = {'policy_domain': category}
        
        # 构建查询文本
        query_parts = [category]
        if subcategory:
            query_parts.append(subcategory)
        
        query = " ".join(query_parts)
        
        return self.search_policies(query, k=k, filters=filters)
    
    def get_policy_by_level(self, level: str, k: int = 10) -> List[Document]:
        """
        按行政层级获取政策
        
        Args:
            level: 行政层级
            k: 返回文档数量
            
        Returns:
            该层级的政策文档
        """
        filters = {'admin_level': level}
        return self.search_policies(level, k=k, filters=filters)
    
    def get_policy_by_year(self, year: str, k: int = 10) -> List[Document]:
        """
        按年份获取政策
        
        Args:
            year: 年份
            k: 返回文档数量
            
        Returns:
            该年份的政策文档
        """
        filters = {'year': year}
        return self.search_policies(f"{year}年政策", k=k, filters=filters)
    
    def get_related_policies(
        self, 
        policy_content: str, 
        k: int = 5,
        exclude_source: Optional[str] = None
    ) -> List[Document]:
        """
        获取相关政策
        
        Args:
            policy_content: 政策内容
            k: 返回文档数量
            exclude_source: 排除的源文件
            
        Returns:
            相关政策列表
        """
        # 提取关键词作为查询
        query = policy_content[:200]  # 使用前200字符作为查询
        
        docs = self.search_policies(query, k=k*2)
        
        # 排除指定源文件
        if exclude_source:
            docs = [doc for doc in docs if doc.metadata.get('source') != exclude_source]
        
        return docs[:k]
    
    def get_knowledge_base_stats(self) -> Dict[str, Any]:
        """获取知识库统计信息"""
        try:
            collection = self.vectorstore._collection
            total_docs = collection.count()
            
            # 获取所有文档的元数据进行统计
            all_docs = self.vectorstore.similarity_search("", k=total_docs)
            
            stats = {
                'total_documents': total_docs,
                'by_admin_level': {},
                'by_policy_domain': {},
                'by_year': {},
                'by_region': {},
                'by_doc_type': {}
            }
            
            for doc in all_docs:
                metadata = doc.metadata
                
                # 统计各维度
                for key in ['admin_level', 'policy_domain', 'year', 'region', 'doc_type']:
                    value = metadata.get(key, '未知')
                    stats[f'by_{key}'][value] = stats[f'by_{key}'].get(value, 0) + 1
            
            return stats
            
        except Exception as e:
            logger.error(f"获取知识库统计失败: {e}")
            return {}
    
    def export_knowledge_base_info(self, output_path: str):
        """导出知识库信息"""
        try:
            stats = self.get_knowledge_base_stats()
            
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(stats, f, ensure_ascii=False, indent=2)
            
            logger.info(f"知识库信息已导出到: {output_path}")
            
        except Exception as e:
            logger.error(f"导出知识库信息失败: {e}")

class PolicyRAGRetriever:
    """政策RAG检索器"""
    
    def __init__(self, rag_system: PolicyRAGSystem):
        """
        初始化检索器
        
        Args:
            rag_system: 政策RAG系统实例
        """
        self.rag_system = rag_system
    
    def retrieve_for_question(
        self, 
        question: str, 
        context: Optional[Dict[str, Any]] = None
    ) -> Tuple[List[Document], Dict[str, Any]]:
        """
        为问题检索相关政策
        
        Args:
            question: 用户问题
            context: 上下文信息（如地区、层级等）
            
        Returns:
            (相关文档列表, 检索元信息)
        """
        # 分析问题类型和关键词
        question_analysis = self._analyze_question(question)
        
        # 构建过滤条件
        filters = self._build_filters(question_analysis, context)
        
        # 检索相关文档
        docs = self.rag_system.search_policies(
            question, 
            k=5, 
            filters=filters
        )
        
        # 构建检索元信息
        retrieval_info = {
            'question_type': question_analysis['type'],
            'keywords': question_analysis['keywords'],
            'filters_applied': filters,
            'documents_found': len(docs)
        }
        
        return docs, retrieval_info
    
    def _analyze_question(self, question: str) -> Dict[str, Any]:
        """分析问题类型和关键词"""
        import re
        
        analysis = {
            'type': 'general',
            'keywords': [],
            'admin_level': None,
            'policy_domain': None,
            'year': None,
            'region': None
        }
        
        # 提取关键词
        chinese_words = re.findall(r'[\u4e00-\u9fff]+', question)
        analysis['keywords'] = [word for word in chinese_words if len(word) > 1]
        
        # 识别行政层级
        level_keywords = {
            '中央': ['中央', '国家', '国务院', '部委'],
            '省级': ['省', '省级', '省政府'],
            '市级': ['市', '市级', '市政府'],
            '区县': ['区', '县', '区县'],
            '街道社区': ['街道', '社区', '村']
        }
        
        for level, keywords in level_keywords.items():
            if any(keyword in question for keyword in keywords):
                analysis['admin_level'] = level
                analysis['type'] = 'level_specific'
                break
        
        # 识别政策领域
        domain_keywords = {
            '基层治理': ['基层', '治理', '社区', '网格', '党建'],
            '民生保障': ['民生', '救助', '养老', '残疾', '儿童'],
            '社会治理': ['平安', '矛盾', '纠纷', '信访', '志愿'],
            '公共服务': ['政务', '便民', '营商', '服务']
        }
        
        for domain, keywords in domain_keywords.items():
            if any(keyword in question for keyword in keywords):
                analysis['policy_domain'] = domain
                analysis['type'] = 'domain_specific'
                break
        
        # 提取年份
        year_matches = re.findall(r'20\d{2}', question)
        if year_matches:
            analysis['year'] = year_matches[0]
            analysis['type'] = 'time_specific'
        
        return analysis
    
    def _build_filters(
        self, 
        question_analysis: Dict[str, Any], 
        context: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """构建过滤条件"""
        filters = {}
        
        # 从问题分析中提取过滤条件
        if question_analysis.get('admin_level'):
            filters['admin_level'] = question_analysis['admin_level']
        
        if question_analysis.get('policy_domain'):
            filters['policy_domain'] = question_analysis['policy_domain']
        
        if question_analysis.get('year'):
            filters['year'] = question_analysis['year']
        
        # 从上下文中提取过滤条件
        if context:
            for key in ['admin_level', 'policy_domain', 'year', 'region']:
                if key in context and context[key]:
                    filters[key] = context[key]
        
        return filters

def build_policy_rag_system(data_dir: str = "./data/optimized") -> PolicyRAGSystem:
    """
    构建政策RAG系统的便捷函数
    
    Args:
        data_dir: 优化后的政策数据目录
        
    Returns:
        政策RAG系统实例
    """
    logger.info("开始构建政策RAG系统...")
    
    try:
        # 创建RAG系统
        rag_system = PolicyRAGSystem()
        
        # 从优化后的数据构建知识库
        success = rag_system.build_knowledge_base_from_optimized_data(data_dir)
        
        if success:
            logger.info("政策RAG系统构建成功")
            return rag_system
        else:
            logger.error("政策RAG系统构建失败")
            return None
            
    except Exception as e:
        logger.error(f"构建政策RAG系统时出错: {e}")
        return None

if __name__ == "__main__":
    # 构建政策RAG系统
    rag_system = build_policy_rag_system()
    
    if rag_system:
        # 获取统计信息
        stats = rag_system.get_knowledge_base_stats()
        print(f"知识库统计: {json.dumps(stats, ensure_ascii=False, indent=2)}")
        
        # 测试搜索
        test_queries = [
            "如何处理邻里纠纷？",
            "养老服务政策有哪些？",
            "基层治理的具体措施",
            "2024年的新政策"
        ]
        
        retriever = PolicyRAGRetriever(rag_system)
        
        for query in test_queries:
            print(f"\n查询: {query}")
            docs, info = retriever.retrieve_for_question(query)
            
            print(f"检索信息: {info}")
            print(f"找到 {len(docs)} 个相关文档:")
            
            for i, doc in enumerate(docs[:3], 1):
                print(f"  {i}. {doc.metadata.get('title', '未知标题')}")
                print(f"     层级: {doc.metadata.get('admin_level', '未知')}")
                print(f"     领域: {doc.metadata.get('policy_domain', '未知')}")
                print(f"     内容: {doc.page_content[:100]}...")
    else:
        print("政策RAG系统构建失败")