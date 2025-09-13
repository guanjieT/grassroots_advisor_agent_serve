"""
政策引擎 - 政策检索和分析模块
负责政策的检索、关联分析和合规性检查
"""
import os
from typing import List, Dict, Any, Optional
from langchain_core.documents import Document
from langchain_community.embeddings import DashScopeEmbeddings
from langchain_chroma import Chroma

from config import config
from utils.logger import logger
from src.governance_agent import PolicyReference, AdminLevel

class PolicyEngine:
    """政策引擎"""
    
    def __init__(self):
        """初始化政策引擎"""
        logger.info("初始化政策引擎...")
        
        # 初始化嵌入模型
        self.embeddings = DashScopeEmbeddings(
            dashscope_api_key=config.DASHSCOPE_API_KEY,
            model=config.EMBEDDING_MODEL
        )
        
        # 政策向量数据库
        self.vectorstore = None
        
        # 初始化向量数据库
        self._initialize_vectorstore()
        
        # 政策层级权重
        self.level_weights = {
            AdminLevel.CENTRAL.value: 1.0,
            AdminLevel.PROVINCIAL.value: 0.8,
            AdminLevel.MUNICIPAL.value: 0.6,
            AdminLevel.COUNTY.value: 0.4,
            AdminLevel.STREET.value: 0.2
        }
        
        logger.info("政策引擎初始化完成")
    
    def _infer_admin_level_from_metadata(self, metadata: Dict[str, Any]) -> str:
        """根据文档元数据推断行政层级"""
        # 优先使用已提供的字段
        admin_level = metadata.get('admin_level')
        if admin_level:
            # 处理实际的元数据格式（如"01_中央政策"）
            if isinstance(admin_level, str):
                if '01_中央政策' in admin_level or '中央' in admin_level:
                    return AdminLevel.CENTRAL.value
                elif '02_省级政策' in admin_level or '省级' in admin_level or '省' in admin_level:
                    return AdminLevel.PROVINCIAL.value
                elif '03_市级政策' in admin_level or '市级' in admin_level or '市' in admin_level:
                    return AdminLevel.MUNICIPAL.value
                elif '04_县级政策' in admin_level or '县级' in admin_level or '县' in admin_level or '区' in admin_level:
                    return AdminLevel.COUNTY.value
                elif '05_街道级政策' in admin_level or '街道级' in admin_level or '街道' in admin_level or '社区' in admin_level:
                    return AdminLevel.STREET.value
                # 如果已经是标准值，直接返回
                elif admin_level in [AdminLevel.CENTRAL.value, AdminLevel.PROVINCIAL.value, 
                                   AdminLevel.MUNICIPAL.value, AdminLevel.COUNTY.value, AdminLevel.STREET.value]:
                    return admin_level

        # 从其他字段推断
        text_candidates = [
            str(metadata.get('authority', '')),
            str(metadata.get('region', '')),
            str(metadata.get('title', '')),
            str(metadata.get('source', '')),
        ]
        combined = ' '.join([t for t in text_candidates if t])

        if any(k in combined for k in ['国务院', '中共中央', '中央办公厅', '国务院办公厅', '中央政策']):
            return AdminLevel.CENTRAL.value
        if any(k in combined for k in ['省', '自治区', '直辖市', '省人民政府', '省政府', '省委', '省办公厅', '省级政策']):
            return AdminLevel.PROVINCIAL.value
        if any(k in combined for k in ['市', '市人民政府', '市政府', '市委', '市办公室', '市级政策']):
            return AdminLevel.MUNICIPAL.value
        if any(k in combined for k in ['区', '县', '区人民政府', '县人民政府', '区政府', '县政府', '县级政策']):
            return AdminLevel.COUNTY.value
        if any(k in combined for k in ['街道', '社区', '镇人民政府', '乡人民政府', '街道办事处', '街道级政策']):
            return AdminLevel.STREET.value

        return AdminLevel.CENTRAL.value  # 默认不明确则按中央处理

    def _extract_location_terms(self, location: str) -> List[str]:
        """从location字符串中提取省/市/区/县/街道等关键词用于地域加权"""
        terms: List[str] = []
        if not location:
            return terms
        # 简单基于分隔和常见后缀抽取
        for suffix in ['自治区', '特别行政区', '省', '市', '区', '县', '街道', '乡', '镇', '社区']:
            idx = location.find(suffix)
            if idx > 0:
                # 含该后缀的词片段
                start = max(0, idx - 6)  # 中文地名一般不超过6字
                fragment = location[start:idx+len(suffix)]
                # 进一步粗略切分，取最后一个连续中文段
                import re
                m = re.findall(r'[\u4e00-\u9fa5]{2,}', fragment)
                if m:
                    terms.extend(m[-2:])
        # 去重保序
        seen = set()
        unique_terms = []
        for t in terms:
            if t not in seen:
                seen.add(t)
                unique_terms.append(t)
        return unique_terms

    def _initialize_vectorstore(self):
        """初始化政策向量数据库（兼容多种历史路径与集合名）"""
        try:
            candidates = [
                # 新体系：使用全局CHROMA目录下的policy_rag + 统一集合名
                (os.path.join(config.CHROMA_PERSIST_DIRECTORY, "policy_rag"), "policy_knowledge_base"),
                # 旧目录：历史使用的独立policy_rag_chroma目录
                ("./data/policy_rag_chroma", "policy_knowledge"),
                # 退路：直接在CHROMA目录下寻找统一集合名
                (config.CHROMA_PERSIST_DIRECTORY, "policy_knowledge_base"),
            ]

            initialized = False
            for persist_dir, collection_name in candidates:
                if not os.path.exists(persist_dir):
                    continue
                try:
                    vs = Chroma(
                        collection_name=collection_name,
                        embedding_function=self.embeddings,
                        persist_directory=persist_dir
                    )
                    # 判断集合是否非空
                    try:
                        collection = vs._collection
                        count = collection.count()
                    except Exception:
                        count = 0
                    self.vectorstore = vs
                    if count and count > 0:
                        logger.info(
                            f"政策向量数据库初始化完成: dir={persist_dir}, collection={collection_name}, count={count}"
                        )
                        initialized = True
                        break
                    else:
                        logger.warning(
                            f"政策向量集合为空: dir={persist_dir}, collection={collection_name}" 
                            + ", 将继续尝试其他候选路径"
                        )
                except Exception as sub_e:
                    logger.warning(f"尝试初始化失败: dir={persist_dir}, collection={collection_name}, error={sub_e}")

            if not initialized and self.vectorstore is not None:
                logger.warning("未找到非空政策集合，当前连接的集合可能为空。请先构建政策RAG系统。")
            if self.vectorstore is None:
                logger.warning("政策向量数据库不存在或不可用，请先构建政策RAG系统")

        except Exception as e:
            logger.error(f"政策向量数据库初始化失败: {e}")
            raise
    
    def find_relevant_policies(
        self, 
        problem_description: str,
        location: str = "",
        admin_levels: Optional[List[str]] = None,
        k: int = 5
    ) -> List[PolicyReference]:
        """
        查找相关政策
        
        Args:
            problem_description: 问题描述
            location: 地区信息
            admin_levels: 行政层级过滤
            k: 返回政策数量
            
        Returns:
            相关政策列表
        """
        try:
            if not self.vectorstore:
                logger.warning("政策向量数据库未初始化")
                return []
            
            logger.info(f"查找相关政策: {problem_description[:50]}...")
            logger.info(f"地区信息: {location}")
            logger.info(f"层级过滤: {admin_levels}")
            
            # 构建查询文本
            query_parts = [problem_description]
            if location:
                query_parts.append(location)
            
            query = " ".join(query_parts)
            logger.info(f"查询文本: {query}")
            
            # 优先使用相关性分数（越大越相关），失败则回退到距离分数
            try:
                docs_with_scores = self.vectorstore.similarity_search_with_relevance_scores(
                    query, k=k*3
                )
                # 统一为 (doc, relevance)
                normalized_results = [(doc, float(score)) for doc, score in docs_with_scores]
                logger.info(f"使用相关性分数，找到 {len(normalized_results)} 个候选文档")
            except Exception as e:
                logger.warning(f"相关性分数检索失败，回退到距离分数: {e}")
                tmp = self.vectorstore.similarity_search_with_score(query, k=k*3)
                normalized_results = []
                for doc, distance in tmp:
                    try:
                        dist = float(distance)
                    except Exception:
                        dist = 1.0
                    relevance = 1.0 / (1.0 + max(dist, 0.0))
                    normalized_results.append((doc, relevance))
                logger.info(f"使用距离分数，找到 {len(normalized_results)} 个候选文档")
            
            # 过滤和排序
            filtered_policies = []
            loc_terms = self._extract_location_terms(location)
            logger.info(f"提取的地域词: {loc_terms}")
            
            for i, (doc, relevance) in enumerate(normalized_results):
                admin_level = self._infer_admin_level_from_metadata(doc.metadata)
                logger.debug(f"文档 {i+1}: 标题={doc.metadata.get('title', 'N/A')}, 层级={admin_level}, 相关性={relevance:.3f}")
                
                # 层级过滤（如果指定了层级且文档层级不在指定范围内，则跳过）
                if admin_levels and admin_level not in admin_levels:
                    logger.debug(f"文档 {i+1} 层级 {admin_level} 不在指定层级 {admin_levels} 中，跳过")
                    continue
                
                # 计算加权相关性分数
                level_weight = self.level_weights.get(admin_level, 0.1)
                region_weight = 1.0
                doc_region = str(doc.metadata.get('region', ''))
                doc_title = str(doc.metadata.get('title', ''))
                if loc_terms and any(term and (term in doc_region or term in doc_title) for term in loc_terms):
                    region_weight = 1.25  # 地域匹配加权
                    logger.debug(f"文档 {i+1} 地域匹配，加权 {region_weight}")
                
                weighted_score = float(relevance) * level_weight * region_weight
                
                # 创建政策参考对象
                policy_ref = PolicyReference(
                    policy_id=doc.metadata.get('source', 'unknown'),
                    title=doc.metadata.get('title', '未知政策'),
                    admin_level=admin_level,
                    relevance_score=weighted_score,
                    key_provisions=self._extract_key_provisions(doc.page_content),
                    compliance_requirements=self._extract_compliance_requirements(doc.page_content),
                    implementation_guidance=self._extract_implementation_guidance(doc.page_content),
                    source=doc.metadata.get('source', 'unknown')
                )
                
                filtered_policies.append(policy_ref)
            
            logger.info(f"层级过滤后剩余 {len(filtered_policies)} 个文档")
            
            # 按加权分数排序并返回前k个
            filtered_policies.sort(key=lambda x: x.relevance_score, reverse=True)
            result = filtered_policies[:k]
            
            logger.info(f"找到 {len(result)} 个相关政策")
            return result
            
        except Exception as e:
            logger.error(f"查找相关政策失败: {e}")
            import traceback
            logger.error(f"详细错误: {traceback.format_exc()}")
            return []
    
    def _extract_key_provisions(self, content: str) -> List[str]:
        """提取关键条款"""
        # 查找包含关键词的句子
        key_keywords = ['规定', '要求', '应当', '必须', '禁止', '条例', '办法']
        
        sentences = content.split('。')
        provisions = []
        
        for sentence in sentences:
            sentence = sentence.strip()
            if any(keyword in sentence for keyword in key_keywords) and len(sentence) > 10:
                provisions.append(sentence + '。')
        
        return provisions[:5]  # 最多5个关键条款
    
    def _extract_compliance_requirements(self, content: str) -> List[str]:
        """提取合规要求"""
        compliance_keywords = ['合规', '依法', '按照', '遵守', '执行', '落实']
        
        sentences = content.split('。')
        requirements = []
        
        for sentence in sentences:
            sentence = sentence.strip()
            if any(keyword in sentence for keyword in compliance_keywords) and len(sentence) > 10:
                requirements.append(sentence + '。')
        
        return requirements[:3]  # 最多3个合规要求
    
    def _extract_implementation_guidance(self, content: str) -> List[str]:
        """提取实施指导"""
        guidance_keywords = ['指导', '建议', '推进', '加强', '完善', '建立']
        
        sentences = content.split('。')
        guidance = []
        
        for sentence in sentences:
            sentence = sentence.strip()
            if any(keyword in sentence for keyword in guidance_keywords) and len(sentence) > 10:
                guidance.append(sentence + '。')
        
        return guidance[:3]  # 最多3个实施指导
    
    def check_policy_compliance(
        self, 
        solution_steps: List[Dict[str, Any]], 
        relevant_policies: List[PolicyReference]
    ) -> Dict[str, Any]:
        """
        检查方案的政策合规性
        
        Args:
            solution_steps: 解决方案步骤
            relevant_policies: 相关政策
            
        Returns:
            合规性检查结果
        """
        try:
            compliance_result = {
                'overall_compliance': 'compliant',  # compliant, warning, non_compliant
                'compliance_score': 0.0,
                'issues': [],
                'recommendations': []
            }
            
            if not relevant_policies:
                compliance_result['overall_compliance'] = 'warning'
                compliance_result['issues'].append('缺少相关政策依据')
                return compliance_result
            
            # 简单的合规性检查逻辑
            total_score = 0
            max_score = len(solution_steps) * len(relevant_policies)
            
            for step in solution_steps:
                step_content = step.get('description', '')
                
                for policy in relevant_policies:
                    # 检查步骤是否与政策要求一致
                    for requirement in policy.compliance_requirements:
                        if self._check_content_alignment(step_content, requirement):
                            total_score += 1
            
            # 计算合规分数
            if max_score > 0:
                compliance_result['compliance_score'] = total_score / max_score
            
            # 确定合规等级
            if compliance_result['compliance_score'] >= 0.8:
                compliance_result['overall_compliance'] = 'compliant'
            elif compliance_result['compliance_score'] >= 0.5:
                compliance_result['overall_compliance'] = 'warning'
                compliance_result['issues'].append('部分步骤可能需要政策依据支撑')
            else:
                compliance_result['overall_compliance'] = 'non_compliant'
                compliance_result['issues'].append('方案与现行政策存在较大差异')
            
            # 生成建议
            if compliance_result['compliance_score'] < 1.0:
                compliance_result['recommendations'].append('建议进一步核实相关政策要求')
                compliance_result['recommendations'].append('考虑咨询法律专业人士')
            
            return compliance_result
            
        except Exception as e:
            logger.error(f"政策合规性检查失败: {e}")
            return {
                'overall_compliance': 'error',
                'compliance_score': 0.0,
                'issues': [f'检查过程出错: {str(e)}'],
                'recommendations': ['建议人工审核政策合规性']
            }
    
    def _check_content_alignment(self, content1: str, content2: str) -> bool:
        """检查两个内容的一致性"""
        # 简单的关键词匹配
        words1 = set(content1.split())
        words2 = set(content2.split())
        
        # 计算交集比例
        intersection = words1.intersection(words2)
        union = words1.union(words2)
        
        if len(union) == 0:
            return False
        
        similarity = len(intersection) / len(union)
        return similarity > 0.1  # 10%以上相似度认为一致
    
    def get_policy_hierarchy(self, location: str) -> List[str]:
        """
        获取特定地区的政策层级
        
        Args:
            location: 地区名称
            
        Returns:
            适用的政策层级列表
        """
        # 根据地区确定适用的政策层级
        hierarchy = [AdminLevel.CENTRAL.value]  # 中央政策总是适用
        
        if '省' in location or '自治区' in location or '直辖市' in location:
            hierarchy.append(AdminLevel.PROVINCIAL.value)
        
        if '市' in location:
            hierarchy.extend([AdminLevel.PROVINCIAL.value, AdminLevel.MUNICIPAL.value])
        
        if '区' in location or '县' in location:
            hierarchy.extend([
                AdminLevel.PROVINCIAL.value, 
                AdminLevel.MUNICIPAL.value, 
                AdminLevel.COUNTY.value
            ])
        
        if '街道' in location or '社区' in location:
            hierarchy.extend([
                AdminLevel.PROVINCIAL.value,
                AdminLevel.MUNICIPAL.value,
                AdminLevel.COUNTY.value,
                AdminLevel.STREET.value
            ])
        
        return list(set(hierarchy))  # 去重
    
    def get_policy_statistics(self) -> Dict[str, Any]:
        """获取政策库统计信息"""
        try:
            if not self.vectorstore:
                return {'error': '政策向量数据库未初始化'}
            
            # 这里需要实现具体的统计逻辑
            # ChromaDB没有直接的统计接口，需要通过查询实现
            return {
                'status': 'active',
                'note': '政策库统计功能需要进一步实现'
            }
            
        except Exception as e:
            logger.error(f"获取政策统计失败: {e}")
            return {'error': str(e)}

if __name__ == "__main__":
    # 测试政策引擎
    try:
        engine = PolicyEngine()
        
        # 获取统计信息
        stats = engine.get_policy_statistics()
        print(f"政策库统计: {stats}")
        
        # 测试政策检索
        test_problem = "小区垃圾分类执行不到位"
        test_location = "广州市天河区"
        
        relevant_policies = engine.find_relevant_policies(
            test_problem, 
            test_location, 
            k=3
        )
        
        print(f"\n测试问题: {test_problem}")
        print(f"测试地区: {test_location}")
        print(f"找到 {len(relevant_policies)} 个相关政策:")
        
        for i, policy in enumerate(relevant_policies, 1):
            print(f"\n{i}. {policy.title}")
            print(f"   层级: {policy.admin_level}")
            print(f"   相关性: {policy.relevance_score:.3f}")
            print(f"   关键条款: {len(policy.key_provisions)} 个")
        
        # 测试政策层级
        hierarchy = engine.get_policy_hierarchy(test_location)
        print(f"\n适用政策层级: {hierarchy}")
        
    except Exception as e:
        print(f"测试失败: {e}")
        import traceback
        traceback.print_exc()