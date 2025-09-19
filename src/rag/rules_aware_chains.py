"""
法规感知的RAG链
结合法规政策和案例数据提供合规建议
"""
from typing import List, Dict, Any, Optional, Generator, Tuple
from langchain_core.documents import Document
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough, RunnableLambda
from langchain_community.chat_models import ChatTongyi

from knowledge_base.vector_store import VectorStoreManager
from utils.logger import logger
from config import config

class RulesAwareRAGChain:
    """法规感知的RAG链"""
    
    def __init__(self, vector_manager: Optional[VectorStoreManager] = None):
        """
        初始化法规感知RAG链
        
        Args:
            vector_manager: 向量数据库管理器
        """
        self.vector_manager = vector_manager or VectorStoreManager()
        
        # 初始化LLM
        self.llm = ChatTongyi(
            dashscope_api_key=config.DASHSCOPE_API_KEY,
            model=config.LLM_MODEL,
            temperature=config.DASHSCOPE_TEMPERATURE,
            max_tokens=config.DASHSCOPE_MAX_TOKENS
        )
        
        # 创建检索器
        self.retriever = self.vector_manager.get_retriever()
        
        # 创建提示模板
        self.prompt_template = self._create_rules_aware_prompt()
        
        # 创建RAG链
        self.rag_chain = self._create_rag_chain()
        
        logger.info("法规感知RAG链初始化完成")
    
    def _create_rules_aware_prompt(self) -> ChatPromptTemplate:
        """创建法规感知的提示模板"""
        
        system_prompt = """你是一位专业的基层工作法律顾问和实务专家，具备深厚的法律知识和丰富的基层工作经验。

你的核心职责：
1. 基于相关法规政策，确保所有建议都符合法律法规要求
2. 结合成功案例经验，提供具体可操作的解决方案
3. 在合规的前提下，追求工作效率和实际效果
4. 对可能的法律风险进行提示和预警

工作原则：
- 合规性优先：所有建议必须符合国家法律法规和地方政策
- 实用性导向：提供具体的操作步骤和实施方案
- 风险防控：识别并提示潜在的法律风险和注意事项
- 因地制宜：考虑不同地区的政策差异和实际情况

参考资料分析：
{context}

请基于以上法规政策和案例资料，为用户问题提供专业、合规、实用的解决建议。

回答格式要求：
1. 法规依据：明确相关的法律法规依据
2. 解决方案：提供具体的操作步骤
3. 注意事项：强调需要注意的合规要点
4. 风险提示：指出可能的风险和防范措施
5. 参考案例：引用相关的成功案例（如有）"""

        prompt_template = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            ("human", "{question}")
        ])
        
        return prompt_template
    
    def _categorize_documents(self, docs: List[Document]) -> Dict[str, List[Document]]:
        """
        将文档按类型分类
        
        Args:
            docs: 检索到的文档列表
            
        Returns:
            分类后的文档字典
        """
        categorized = {
            'regulations': [],  # 法规政策
            'cases': [],        # 案例
            'policies': []      # 地方政策
        }
        
        for doc in docs:
            doc_type = doc.metadata.get('type', 'unknown')
            if doc_type == 'regulation':
                categorized['regulations'].append(doc)
            elif doc_type == 'case':
                categorized['cases'].append(doc)
            elif doc_type == 'policy':
                categorized['policies'].append(doc)
            else:
                # 默认归类为案例
                categorized['cases'].append(doc)
        
        return categorized
    
    def _format_categorized_docs(self, categorized_docs: Dict[str, List[Document]]) -> str:
        """
        格式化分类后的文档
        
        Args:
            categorized_docs: 分类后的文档
            
        Returns:
            格式化后的文档内容
        """
        formatted_sections = []
        
        # 1. 法规政策部分
        if categorized_docs['regulations']:
            reg_section = ["【相关法规政策】"]
            for i, doc in enumerate(categorized_docs['regulations'][:3], 1):
                title = doc.metadata.get('title', '未知法规')
                authority = doc.metadata.get('authority', '未知机关')
                content = doc.page_content[:500] + "..." if len(doc.page_content) > 500 else doc.page_content
                
                reg_section.append(f"{i}. {title}")
                reg_section.append(f"   发布机关: {authority}")
                reg_section.append(f"   主要内容: {content}")
                reg_section.append("")
            
            formatted_sections.append("\n".join(reg_section))
        
        # 2. 地方政策部分
        if categorized_docs['policies']:
            policy_section = ["【地方政策文件】"]
            for i, doc in enumerate(categorized_docs['policies'][:2], 1):
                title = doc.metadata.get('title', '未知政策')
                region = doc.metadata.get('region', '未知地区')
                content = doc.page_content[:400] + "..." if len(doc.page_content) > 400 else doc.page_content
                
                policy_section.append(f"{i}. {title} ({region})")
                policy_section.append(f"   内容: {content}")
                policy_section.append("")
            
            formatted_sections.append("\n".join(policy_section))
        
        # 3. 成功案例部分
        if categorized_docs['cases']:
            case_section = ["【相关成功案例】"]
            for i, doc in enumerate(categorized_docs['cases'][:3], 1):
                title = doc.metadata.get('title', '未知案例')
                category = doc.metadata.get('category', '未知类别')
                content = doc.page_content[:400] + "..." if len(doc.page_content) > 400 else doc.page_content
                
                case_section.append(f"{i}. {title} ({category})")
                case_section.append(f"   案例内容: {content}")
                case_section.append("")
            
            formatted_sections.append("\n".join(case_section))
        
        if not formatted_sections:
            return "未找到相关的法规政策和案例资料。"
        
        return "\n" + "="*80 + "\n".join(formatted_sections)
    
    def _create_rag_chain(self):
        """创建法规感知的RAG链"""
        
        def retrieve_and_categorize(question):
            """检索并分类文档"""
            # 使用新的 invoke 方法替代已弃用的 get_relevant_documents
            docs = self.retriever.invoke(question)
            categorized = self._categorize_documents(docs)
            return self._format_categorized_docs(categorized)
        
        # 构建RAG链
        rag_chain = (
            {
                "context": RunnableLambda(retrieve_and_categorize),
                "question": RunnablePassthrough()
            }
            | self.prompt_template
            | self.llm
            | StrOutputParser()
        )
        
        return rag_chain
    
    def invoke(self, question: str) -> str:
        """
        调用法规感知RAG链生成回答
        
        Args:
            question: 用户问题
            
        Returns:
            生成的回答
        """
        try:
            logger.info(f"处理法规感知问题: {question}")
            
            # 调用RAG链
            response = self.rag_chain.invoke(question)
            
            logger.info("法规感知问题处理完成")
            return response
            
        except Exception as e:
            logger.error(f"法规感知RAG链调用失败: {e}")
            return f"抱歉，处理您的问题时出现错误: {str(e)}"
    
    def get_relevant_materials(self, question: str, k: int = 5) -> Dict[str, List[Document]]:
        """
        获取相关的法规政策和案例材料
        
        Args:
            question: 用户问题
            k: 返回文档数量
            
        Returns:
            分类后的相关材料
        """
        try:
            # 使用新的 invoke 方法替代已弃用的 get_relevant_documents
            docs = self.retriever.invoke(question)[:k]
            return self._categorize_documents(docs)
        except Exception as e:
            logger.error(f"获取相关材料失败: {e}")
            return {'regulations': [], 'cases': [], 'policies': []}
    
    def get_relevant_cases(self, question: str, k: int = 3) -> List[Document]:
        """
        获取相关案例（用于调试和展示）
        
        Args:
            question: 用户问题
            k: 返回案例数量
            
        Returns:
            相关案例列表
        """
        try:
            # 使用新的 invoke 方法替代已弃用的 get_relevant_documents
            docs = self.retriever.invoke(question)
            return docs[:k]
        except Exception as e:
            logger.error(f"获取相关案例失败: {e}")
            return []
    
    def check_compliance(self, proposed_solution: str, context: str) -> str:
        """
        检查方案的合规性
        
        Args:
            proposed_solution: 提议的解决方案
            context: 问题上下文
            
        Returns:
            合规性检查结果
        """
        try:
            compliance_prompt = f"""
            作为法律合规专家，请检查以下解决方案的合规性：
            
            问题背景：{context}
            
            提议方案：{proposed_solution}
            
            请从以下方面进行合规性分析：
            1. 是否符合相关法律法规
            2. 是否存在法律风险
            3. 需要注意的合规要点
            4. 建议的改进措施
            
            请提供详细的合规性分析报告。
            """
            
            response = self.llm.invoke([{"role": "user", "content": compliance_prompt}])
            return response.content
            
        except Exception as e:
            logger.error(f"合规性检查失败: {e}")
            return f"合规性检查时出现错误: {str(e)}"

class ComplianceChecker:
    """合规性检查器"""
    
    def __init__(self, rules_chain: RulesAwareRAGChain):
        self.rules_chain = rules_chain
    
    def validate_solution(self, question: str, solution: str) -> Dict[str, Any]:
        """
        验证解决方案的合规性
        
        Args:
            question: 原始问题
            solution: 提议的解决方案
            
        Returns:
            验证结果
        """
        try:
            # 获取相关法规材料
            materials = self.rules_chain.get_relevant_materials(question)
            
            # 检查合规性
            compliance_result = self.rules_chain.check_compliance(solution, question)
            
            # 统计相关材料
            material_count = {
                'regulations': len(materials['regulations']),
                'policies': len(materials['policies']),
                'cases': len(materials['cases'])
            }
            
            return {
                'compliance_check': compliance_result,
                'relevant_materials': materials,
                'material_count': material_count,
                'validation_passed': True
            }
            
        except Exception as e:
            logger.error(f"解决方案验证失败: {e}")
            return {
                'error': str(e),
                'validation_passed': False
            }

if __name__ == "__main__":
    # 测试法规感知RAG链
    try:
        rules_rag = RulesAwareRAGChain()
        
        test_questions = [
            "处理邻里纠纷时需要遵循哪些法律程序？",
            "社区网格化管理的法律依据是什么？",
            "困难家庭救助申请的政策规定有哪些？"
        ]
        
        print("=== 法规感知RAG链测试 ===")
        for question in test_questions:
            print(f"\n问题: {question}")
            answer = rules_rag.invoke(question)
            print(f"回答: {answer[:300]}...")
            
            # 获取相关材料统计
            materials = rules_rag.get_relevant_materials(question)
            print(f"相关材料: 法规{len(materials['regulations'])}个, 政策{len(materials['policies'])}个, 案例{len(materials['cases'])}个")
        
    except Exception as e:
        print(f"测试失败: {e}")
        logger.error(f"法规感知RAG链测试失败: {e}")