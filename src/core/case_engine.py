"""
案例引擎 - 核心案例检索和分析模块
负责案例的加载、索引、检索和相似度分析
"""
import os
import json
import numpy as np
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import asdict
from langchain_core.documents import Document
from langchain_community.embeddings import DashScopeEmbeddings
from langchain_chroma import Chroma
from langchain_text_splitters import RecursiveCharacterTextSplitter

from config import config
from utils.logger import logger
from src.governance_agent import CaseReference, ProblemType

class CaseEngine:
    """案例引擎 - 系统核心组件"""
    
    def __init__(self):
        """初始化案例引擎"""
        logger.info("初始化案例引擎...")
        
        # 初始化嵌入模型
        self.embeddings = DashScopeEmbeddings(
            dashscope_api_key=config.DASHSCOPE_API_KEY,
            model=config.EMBEDDING_MODEL
        )
        
        # 文档分割器
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=800,
            chunk_overlap=100,
            length_function=len,
            separators=["\n\n", "\n", "。", "；", "，", " ", ""]
        )
        
        # 案例向量数据库
        self.vectorstore = None
        self.case_metadata = {}  # 案例元数据缓存
        
        # 初始化向量数据库
        self._initialize_vectorstore()
        
        # 加载案例数据
        self._load_cases()
        
        logger.info("案例引擎初始化完成")
    
    def _initialize_vectorstore(self):
        """初始化向量数据库"""
        try:
            persist_dir = "./data/case_engine_vectorstore"
            os.makedirs(persist_dir, exist_ok=True)
            
            self.vectorstore = Chroma(
                collection_name="governance_cases",
                embedding_function=self.embeddings,
                persist_directory=persist_dir
            )
            
            logger.info("案例向量数据库初始化完成")
            
        except Exception as e:
            logger.error(f"案例向量数据库初始化失败: {e}")
            raise
    
    def _load_cases(self):
        """加载案例数据"""
        try:
            logger.info("开始加载案例数据...")
            
            # 清空现有数据
            self._clear_vectorstore()
            
            # 加载不同来源的案例
            all_documents = []
            
            # 1. 加载JSON样本案例
            json_cases = self._load_json_cases()
            all_documents.extend(json_cases)
            
            # 2. 加载DOC/DOCX案例文档
            doc_cases = self._load_document_cases()
            all_documents.extend(doc_cases)
            
            if not all_documents:
                logger.warning("没有找到有效的案例数据")
                return
            
            # 添加到向量数据库
            batch_size = 50
            for i in range(0, len(all_documents), batch_size):
                batch = all_documents[i:i + batch_size]
                self.vectorstore.add_documents(batch)
                logger.info(f"已处理 {min(i + batch_size, len(all_documents))}/{len(all_documents)} 个案例")
            
            logger.info(f"案例数据加载完成，共 {len(all_documents)} 个案例")
            
        except Exception as e:
            logger.error(f"加载案例数据失败: {e}")
            raise
    
    def _load_json_cases(self) -> List[Document]:
        """加载JSON格式的样本案例"""
        documents = []
        
        json_file = "./data/knowledge_base/sample_cases.json"
        if not os.path.exists(json_file):
            logger.warning(f"JSON案例文件不存在: {json_file}")
            return documents
        
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                cases = json.load(f)
            
            for case in cases:
                # 格式化案例内容
                content = self._format_case_content(case)
                
                # 限制内容长度
                if len(content) > 6000:
                    content = content[:6000] + "..."
                
                # 创建文档
                doc = Document(
                    page_content=content,
                    metadata={
                        'case_id': case['id'],
                        'title': case['title'],
                        'category': case['category'],
                        'problem_type': self._map_category_to_problem_type(case['category']),
                        'source': 'sample_cases',
                        'keywords': ','.join(case.get('keywords', [])),
                        'success_factors': case.get('reflection', ''),
                        'measures': '; '.join(case.get('steps', []))
                    }
                )
                
                documents.append(doc)
                
                # 缓存元数据
                self.case_metadata[case['id']] = case
            
            logger.info(f"加载JSON案例: {len(documents)} 个")
            
        except Exception as e:
            logger.error(f"加载JSON案例失败: {e}")
        
        return documents
    
    def _load_document_cases(self) -> List[Document]:
        """加载DOC/DOCX格式的案例文档"""
        documents = []
        
        try:
            from knowledge_base.doc_processor import DocProcessor
            
            processor = DocProcessor()
            case_dir = "./data/knowledge_base/已有案例"
            
            if os.path.exists(case_dir):
                doc_documents = processor.process_doc_files(case_dir)
                
                for doc in doc_documents:
                    # 添加额外的元数据
                    doc.metadata.update({
                        'problem_type': self._map_category_to_problem_type(doc.metadata.get('category', '其他')),
                        'success_factors': self._extract_success_factors(doc.page_content),
                        'measures': self._extract_measures(doc.page_content)
                    })
                    
                    documents.append(doc)
                    
                    # 缓存元数据
                    case_id = doc.metadata.get('filename', f"doc_{len(self.case_metadata)}")
                    self.case_metadata[case_id] = {
                        'id': case_id,
                        'title': doc.metadata.get('title', '未知'),
                        'category': doc.metadata.get('category', '其他'),
                        'content': doc.page_content
                    }
                
                logger.info(f"加载文档案例: {len(documents)} 个")
            
        except Exception as e:
            logger.error(f"加载文档案例失败: {e}")
        
        return documents
    
    def _format_case_content(self, case: Dict[str, Any]) -> str:
        """格式化案例内容"""
        content_parts = [
            f"案例标题：{case['title']}",
            f"案例类别：{case['category']}",
            f"问题描述：{case['problem']}",
            "解决步骤："
        ]
        
        for i, step in enumerate(case.get('steps', []), 1):
            content_parts.append(f"{i}. {step}")
        
        content_parts.extend([
            f"解决结果：{case.get('result', '')}",
            f"经验总结：{case.get('reflection', '')}",
            f"关键词：{', '.join(case.get('keywords', []))}"
        ])
        
        return '\n'.join(content_parts)
    
    def _map_category_to_problem_type(self, category: str) -> str:
        """将案例类别映射到问题类型"""
        mapping = {
            '邻里纠纷': ProblemType.NEIGHBOR_DISPUTE.value,
            '民生服务': ProblemType.COMMUNITY_SERVICE.value,
            '社区治理': ProblemType.COMMUNITY_SERVICE.value,
            '政策宣传': ProblemType.POLICY_PROMOTION.value,
            '环境治理': ProblemType.ENVIRONMENT_GOVERNANCE.value,
            '安全管理': ProblemType.SAFETY_MANAGEMENT.value,
            '养老服务': ProblemType.ELDERLY_SERVICE.value,
            '停车管理': ProblemType.PARKING_MANAGEMENT.value
        }
        
        return mapping.get(category, ProblemType.OTHER.value)
    
    def _extract_success_factors(self, content: str) -> str:
        """从内容中提取成功因素"""
        # 简单的关键词提取
        success_keywords = ['关键', '成功', '经验', '要点', '核心', '重要']
        
        lines = content.split('\n')
        success_lines = []
        
        for line in lines:
            if any(keyword in line for keyword in success_keywords):
                success_lines.append(line.strip())
        
        return '; '.join(success_lines[:3])  # 最多3个关键因素
    
    def _extract_measures(self, content: str) -> str:
        """从内容中提取具体措施"""
        # 提取步骤性内容
        lines = content.split('\n')
        measures = []
        
        for line in lines:
            line = line.strip()
            # 匹配数字开头的步骤
            if line and (line[0].isdigit() or line.startswith('第') or '步骤' in line):
                measures.append(line)
        
        return '; '.join(measures[:5])  # 最多5个措施
    
    def _clear_vectorstore(self):
        """清空向量数据库"""
        try:
            self.vectorstore.delete_collection()
            self._initialize_vectorstore()
            self.case_metadata.clear()
            logger.info("案例向量数据库已清空")
        except Exception as e:
            logger.warning(f"清空向量数据库失败: {e}")
    
    def find_similar_cases(
        self, 
        problem_description: str, 
        problem_type: Optional[str] = None,
        k: int = 5
    ) -> List[CaseReference]:
        """
        查找相似案例
        
        Args:
            problem_description: 问题描述
            problem_type: 问题类型过滤
            k: 返回案例数量
            
        Returns:
            相似案例列表
        """
        try:
            logger.info(f"查找相似案例: {problem_description[:50]}...")
            
            # 检索相似文档（使用相关性分数，分数越大越相关）
            try:
                docs_with_scores = self.vectorstore.similarity_search_with_relevance_scores(
                    problem_description, k=k*3
                )
                # 统一结果为 (doc, score) 形式
                normalized_results = [(doc, float(score)) for doc, score in docs_with_scores]
            except Exception:
                # 回退到距离分数（分数越小越相似）
                tmp = self.vectorstore.similarity_search_with_score(
                    problem_description, k=k*3
                )
                # 将距离分数转换为相对相关性分数，避免排序反向
                # relevance ~= 1 / (1 + distance)
                normalized_results = []
                for doc, distance in tmp:
                    try:
                        dist = float(distance)
                    except Exception:
                        dist = 1.0
                    relevance = 1.0 / (1.0 + max(dist, 0.0))
                    normalized_results.append((doc, relevance))

            # 过滤和排序
            filtered_cases = []
            for doc, relevance in normalized_results:
                # 类型过滤
                if problem_type and doc.metadata.get('problem_type') != problem_type:
                    continue
                
                # 创建案例参考对象
                case_ref = CaseReference(
                    case_id=doc.metadata.get('case_id', doc.metadata.get('filename', 'unknown')),
                    title=doc.metadata.get('title', '未知案例'),
                    problem_type=doc.metadata.get('problem_type', '其他'),
                    similarity_score=float(relevance),
                    key_measures=self._parse_measures(doc.metadata.get('measures', '')),
                    success_factors=self._parse_success_factors(doc.metadata.get('success_factors', '')),
                    applicable_conditions=self._extract_applicable_conditions(doc.page_content),
                    source=doc.metadata.get('source', 'unknown')
                )
                
                filtered_cases.append(case_ref)
            
            # 按相关性排序并返回前k个
            filtered_cases.sort(key=lambda x: x.similarity_score, reverse=True)
            result = filtered_cases[:k]
            
            logger.info(f"找到 {len(result)} 个相似案例")
            return result
            
        except Exception as e:
            logger.error(f"查找相似案例失败: {e}")
            return []
    
    def _parse_measures(self, measures_text: str) -> List[str]:
        """解析措施文本"""
        if not measures_text:
            return []
        
        measures = measures_text.split(';')
        return [m.strip() for m in measures if m.strip()][:5]
    
    def _parse_success_factors(self, factors_text: str) -> List[str]:
        """解析成功因素文本"""
        if not factors_text:
            return []
        
        factors = factors_text.split(';')
        return [f.strip() for f in factors if f.strip()][:3]
    
    def _extract_applicable_conditions(self, content: str) -> List[str]:
        """提取适用条件"""
        # 简单的条件提取逻辑
        condition_keywords = ['适用', '条件', '前提', '要求', '环境']
        
        lines = content.split('\n')
        conditions = []
        
        for line in lines:
            if any(keyword in line for keyword in condition_keywords):
                conditions.append(line.strip())
        
        return conditions[:3]  # 最多3个条件
    
    def get_case_details(self, case_id: str) -> Optional[Dict[str, Any]]:
        """获取案例详细信息"""
        return self.case_metadata.get(case_id)
    
    def get_case_statistics(self) -> Dict[str, Any]:
        """获取案例库统计信息"""
        try:
            total_cases = len(self.case_metadata)
            
            # 按类型统计
            type_stats = {}
            for case_data in self.case_metadata.values():
                case_type = case_data.get('category', '其他')
                type_stats[case_type] = type_stats.get(case_type, 0) + 1
            
            return {
                'total_cases': total_cases,
                'by_type': type_stats,
                'vectorstore_status': 'active' if self.vectorstore else 'inactive'
            }
            
        except Exception as e:
            logger.error(f"获取案例统计失败: {e}")
            return {'error': str(e)}

if __name__ == "__main__":
    # 测试案例引擎
    try:
        engine = CaseEngine()
        
        # 获取统计信息
        stats = engine.get_case_statistics()
        print(f"案例库统计: {stats}")
        
        # 测试案例检索
        test_problem = "小区内经常有居民遛狗不拴绳，其他居民感到害怕"
        similar_cases = engine.find_similar_cases(test_problem, k=3)
        
        print(f"\n测试问题: {test_problem}")
        print(f"找到 {len(similar_cases)} 个相似案例:")
        
        for i, case in enumerate(similar_cases, 1):
            print(f"\n{i}. {case.title}")
            print(f"   类型: {case.problem_type}")
            print(f"   相似度: {case.similarity_score:.3f}")
            print(f"   关键措施: {case.key_measures[:2]}")
            
    except Exception as e:
        print(f"测试失败: {e}")
        import traceback
        traceback.print_exc()