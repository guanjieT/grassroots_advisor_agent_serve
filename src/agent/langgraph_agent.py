"""
基于LangGraph的基层工作智能辅助Agent
实现检索-评估-反思-再检索-生成的复杂工作流
"""
import json
from typing import TypedDict, Annotated, List, Dict, Any, Optional, Literal
from dataclasses import dataclass, asdict

from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage
from langchain_core.tools import tool
from langchain_community.chat_models import ChatTongyi
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode

from langchain_openai import ChatOpenAI

from knowledge_base.vector_store import VectorStoreManager
from rag.chains import RAGChain
from rag.rules_aware_chains import RulesAwareRAGChain, ComplianceChecker
from utils.logger import logger
from config import config

# 定义Agent状态
class AgentState(TypedDict):
    """Agent状态定义"""
    messages: Annotated[List[BaseMessage], add_messages]
    question: str
    retrieved_cases: List[Dict[str, Any]]
    analysis_result: Dict[str, Any]
    solution_draft: str
    final_solution: str
    reflection_notes: str
    iteration_count: int
    max_iterations: int

@dataclass
class CaseAnalysis:
    """案例分析结果"""
    relevance_score: float
    key_insights: List[str]
    applicable_methods: List[str]
    potential_challenges: List[str]
    success_factors: List[str]

class GrassrootsAdvisorAgent:
    """基层工作智能辅助Agent"""
    
    def __init__(self, use_rules: bool = True):
        """
        初始化Agent
        
        Args:
            use_rules: 是否启用法规感知功能
        """
        self.vector_manager = VectorStoreManager()
        self.use_rules = use_rules
        
        # 初始化RAG链
        if use_rules:
            self.rag_chain = RulesAwareRAGChain(self.vector_manager)
            self.compliance_checker = ComplianceChecker(self.rag_chain)
        else:
            self.rag_chain = RAGChain(self.vector_manager)
            self.compliance_checker = None
        
        # 初始化LLM
        self.llm = ChatTongyi(
            dashscope_api_key=config.DASHSCOPE_API_KEY,
            model=config.LLM_MODEL,
            temperature=config.DASHSCOPE_TEMPERATURE,
            max_tokens=config.DASHSCOPE_MAX_TOKENS
        )
        
        # 创建工具
        self.tools = self._create_tools()
        
        # 创建工作流图
        self.graph = self._create_workflow()
        
        logger.info(f"基层工作智能辅助Agent初始化完成 (法规感知: {'启用' if use_rules else '禁用'})")
    
    def _create_tools(self) -> List:
        """创建Agent工具"""
        
        @tool
        def search_relevant_cases(query: str, k: int = 5) -> str:
            """
            搜索相关案例
            
            Args:
                query: 搜索查询
                k: 返回案例数量
            
            Returns:
                搜索结果的JSON字符串
            """
            try:
                docs = self.vector_manager.search_similar_documents(query, k=k)
                
                cases = []
                for doc in docs:
                    case = {
                        "title": doc.metadata.get("title", "未知标题"),
                        "category": doc.metadata.get("category", "未知类别"),
                        "content": doc.page_content,
                        "case_id": doc.metadata.get("case_id", "未知ID")
                    }
                    cases.append(case)
                
                return json.dumps(cases, ensure_ascii=False, indent=2)
                
            except Exception as e:
                logger.error(f"搜索案例失败: {e}")
                return json.dumps({"error": str(e)}, ensure_ascii=False)
        
        @tool
        def analyze_case_relevance(case_content: str, user_question: str) -> str:
            """
            分析案例与问题的相关性
            
            Args:
                case_content: 案例内容
                user_question: 用户问题
            
            Returns:
                分析结果的JSON字符串
            """
            try:
                analysis_prompt = f"""
                作为基层工作专家，请分析以下案例与用户问题的相关性：
                
                用户问题：{user_question}
                
                案例内容：{case_content}
                
                请从以下方面进行分析：
                1. 相关性评分（0-10分）
                2. 关键洞察（3-5个要点）
                3. 可应用的方法（具体操作）
                4. 潜在挑战（可能遇到的问题）
                5. 成功要素（关键成功因素）
                
                请以JSON格式返回分析结果。
                """
                
                response = self.llm.invoke([HumanMessage(content=analysis_prompt)])
                
                # 尝试解析JSON，如果失败则返回原始文本
                try:
                    return response.content
                except:
                    return json.dumps({
                        "relevance_score": 7,
                        "analysis": response.content
                    }, ensure_ascii=False)
                    
            except Exception as e:
                logger.error(f"案例分析失败: {e}")
                return json.dumps({"error": str(e)}, ensure_ascii=False)
        
        @tool
        def generate_solution_draft(question: str, analyzed_cases: str) -> str:
            """
            基于分析结果生成解决方案草案
            
            Args:
                question: 用户问题
                analyzed_cases: 分析过的案例
            
            Returns:
                解决方案草案
            """
            try:
                draft_prompt = f"""
                基于以下分析过的案例，为用户问题生成一个详细的解决方案草案：
                
                用户问题：{question}
                
                案例分析：{analyzed_cases}
                
                请生成包含以下内容的解决方案：
                1. 问题分析（核心问题是什么）
                2. 解决步骤（具体的操作步骤）
                3. 注意事项（需要特别关注的点）
                4. 预期效果（可能的结果）
                5. 风险提示（可能的风险和应对）
                
                语言要通俗易懂，操作性强。
                """
                
                response = self.llm.invoke([HumanMessage(content=draft_prompt)])
                return response.content
                
            except Exception as e:
                logger.error(f"生成解决方案草案失败: {e}")
                return f"生成解决方案时出现错误: {str(e)}"
        
        @tool
        def reflect_and_improve(solution_draft: str, original_question: str) -> str:
            """
            反思并改进解决方案
            
            Args:
                solution_draft: 解决方案草案
                original_question: 原始问题
            
            Returns:
                改进建议和最终方案
            """
            try:
                # 如果启用了法规感知，进行合规性检查
                compliance_note = ""
                if self.use_rules and self.compliance_checker:
                    try:
                        validation_result = self.compliance_checker.validate_solution(
                            original_question, solution_draft
                        )
                        if validation_result.get('validation_passed'):
                            compliance_note = f"\n\n【合规性检查】\n{validation_result['compliance_check']}"
                    except Exception as e:
                        logger.warning(f"合规性检查失败: {e}")
                
                reflection_prompt = f"""
                请对以下解决方案进行反思和改进：
                
                原始问题：{original_question}
                
                当前方案：{solution_draft}
                
                请从以下角度进行反思：
                1. 方案的完整性（是否遗漏重要步骤）
                2. 可操作性（是否具体可执行）
                3. 实用性（是否贴合基层工作实际）
                4. 合规性（是否符合法律法规要求）
                5. 风险考虑（是否充分考虑风险）
                6. 创新性（是否有更好的方法）
                
                {compliance_note}
                
                请提供改进后的最终方案，确保方案既实用又合规。
                """
                
                response = self.llm.invoke([HumanMessage(content=reflection_prompt)])
                return response.content
                
            except Exception as e:
                logger.error(f"反思改进失败: {e}")
                return f"反思改进时出现错误: {str(e)}"
        
        return [search_relevant_cases, analyze_case_relevance, generate_solution_draft, reflect_and_improve]
    
    def _create_workflow(self) -> StateGraph:
        """创建工作流图"""
        
        # 定义节点函数
        def retrieve_cases_node(state: AgentState) -> AgentState:
            """检索相关案例节点"""
            logger.info("开始检索相关案例")
            
            question = state["question"]
            
            # 使用工具搜索案例
            search_tool = self.tools[0]  # search_relevant_cases
            cases_json = search_tool.invoke({"query": question, "k": 5})
            
            try:
                retrieved_cases = json.loads(cases_json)
                if isinstance(retrieved_cases, dict) and "error" in retrieved_cases:
                    retrieved_cases = []
            except:
                retrieved_cases = []
            
            logger.info(f"检索到 {len(retrieved_cases)} 个相关案例")
            
            return {
                "retrieved_cases": retrieved_cases,
                "messages": [AIMessage(content=f"已检索到 {len(retrieved_cases)} 个相关案例")]
            }
        
        def analyze_cases_node(state: AgentState) -> AgentState:
            """分析案例节点"""
            logger.info("开始分析案例相关性")
            
            question = state["question"]
            retrieved_cases = state["retrieved_cases"]
            
            if not retrieved_cases:
                return {
                    "analysis_result": {"total_cases": 0, "analyses": []},
                    "messages": [AIMessage(content="未找到相关案例，将基于一般经验提供建议")]
                }
            
            # 分析每个案例
            analyze_tool = self.tools[1]  # analyze_case_relevance
            analyses = []
            
            for case in retrieved_cases[:3]:  # 分析前3个最相关的案例
                case_content = f"标题: {case['title']}\n内容: {case['content']}"
                analysis_result = analyze_tool.invoke({
                    "case_content": case_content,
                    "user_question": question
                })
                
                try:
                    analysis_data = json.loads(analysis_result)
                    analyses.append({
                        "case_title": case["title"],
                        "analysis": analysis_data
                    })
                except:
                    analyses.append({
                        "case_title": case["title"],
                        "analysis": {"raw_analysis": analysis_result}
                    })
            
            analysis_result = {
                "total_cases": len(retrieved_cases),
                "analyses": analyses
            }
            
            logger.info(f"完成 {len(analyses)} 个案例的分析")
            
            return {
                "analysis_result": analysis_result,
                "messages": [AIMessage(content=f"已分析 {len(analyses)} 个案例的相关性")]
            }
        
        def generate_solution_node(state: AgentState) -> AgentState:
            """生成解决方案节点"""
            logger.info("开始生成解决方案")
            
            question = state["question"]
            analysis_result = state["analysis_result"]
            
            # 生成解决方案草案
            generate_tool = self.tools[2]  # generate_solution_draft
            solution_draft = generate_tool.invoke({
                "question": question,
                "analyzed_cases": json.dumps(analysis_result, ensure_ascii=False)
            })
            
            logger.info("解决方案草案生成完成")
            
            return {
                "solution_draft": solution_draft,
                "messages": [AIMessage(content="已生成解决方案草案")]
            }
        
        def reflect_and_improve_node(state: AgentState) -> AgentState:
            """反思和改进节点"""
            logger.info("开始反思和改进方案")
            
            question = state["question"]
            solution_draft = state["solution_draft"]
            iteration_count = state.get("iteration_count", 0)
            
            # 反思和改进
            reflect_tool = self.tools[3]  # reflect_and_improve
            final_solution = reflect_tool.invoke({
                "solution_draft": solution_draft,
                "original_question": question
            })
            
            logger.info("方案反思和改进完成")
            
            return {
                "final_solution": final_solution,
                "iteration_count": iteration_count + 1,
                "messages": [AIMessage(content="已完成方案反思和改进")]
            }
        
        def should_continue(state: AgentState) -> Literal["reflect", "end"]:
            """决定是否需要继续迭代"""
            iteration_count = state.get("iteration_count", 0)
            max_iterations = state.get("max_iterations", 1)
            
            if iteration_count < max_iterations:
                return "reflect"
            else:
                return "end"
        
        # 创建状态图
        workflow = StateGraph(AgentState)
        
        # 添加节点
        workflow.add_node("retrieve", retrieve_cases_node)
        workflow.add_node("analyze", analyze_cases_node)
        workflow.add_node("generate", generate_solution_node)
        workflow.add_node("reflect", reflect_and_improve_node)
        
        # 设置入口点
        workflow.set_entry_point("retrieve")
        
        # 添加边
        workflow.add_edge("retrieve", "analyze")
        workflow.add_edge("analyze", "generate")
        workflow.add_edge("generate", "reflect")
        
        # 添加条件边
        workflow.add_conditional_edges(
            "reflect",
            should_continue,
            {
                "reflect": "reflect",
                "end": END
            }
        )
        
        return workflow.compile()
    
    def solve_problem(self, question: str, max_iterations: int = 1) -> Dict[str, Any]:
        """
        解决问题的主要接口
        
        Args:
            question: 用户问题
            max_iterations: 最大迭代次数
        
        Returns:
            包含解决方案和分析过程的字典
        """
        try:
            logger.info(f"开始处理问题: {question}")
            
            # 初始化状态
            initial_state = {
                "messages": [HumanMessage(content=question)],
                "question": question,
                "retrieved_cases": [],
                "analysis_result": {},
                "solution_draft": "",
                "final_solution": "",
                "reflection_notes": "",
                "iteration_count": 0,
                "max_iterations": max_iterations
            }
            
            # 运行工作流
            final_state = self.graph.invoke(initial_state)
            
            logger.info("问题处理完成")
            
            # 整理结果
            result = {
                "question": question,
                "retrieved_cases": final_state.get("retrieved_cases", []),
                "analysis_result": final_state.get("analysis_result", {}),
                "solution_draft": final_state.get("solution_draft", ""),
                "final_solution": final_state.get("final_solution", ""),
                "iteration_count": final_state.get("iteration_count", 0),
                "success": True
            }
            
            return result
            
        except Exception as e:
            logger.error(f"问题处理失败: {e}")
            return {
                "question": question,
                "error": str(e),
                "success": False
            }
    
    def get_simple_answer(self, question: str) -> str:
        """
        获取简单回答（直接使用RAG链）
        
        Args:
            question: 用户问题
        
        Returns:
            回答文本
        """
        try:
            return self.rag_chain.invoke(question)
        except Exception as e:
            logger.error(f"简单回答生成失败: {e}")
            return f"抱歉，处理您的问题时出现错误: {str(e)}"

if __name__ == "__main__":
    # 测试Agent
    try:
        agent = GrassrootsAdvisorAgent()
        
        # 测试复杂工作流
        test_question = "我们社区老人较多，如何更好地开展政策宣传工作，提高老年人对新政策的理解和参与度？"
        
        print(f"问题: {test_question}")
        print("\n=== 使用复杂工作流 ===")
        
        result = agent.solve_problem(test_question, max_iterations=1)
        
        if result["success"]:
            print(f"\n检索到案例数: {len(result['retrieved_cases'])}")
            print(f"\n最终解决方案:\n{result['final_solution']}")
        else:
            print(f"处理失败: {result['error']}")
        
        print("\n=== 使用简单RAG ===")
        simple_answer = agent.get_simple_answer(test_question)
        print(f"\n简单回答:\n{simple_answer}")
        
    except Exception as e:
        print(f"测试失败: {e}")
        logger.error(f"Agent测试失败: {e}") 