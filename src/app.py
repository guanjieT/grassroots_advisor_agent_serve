"""
基层工作智能辅助Agent - Streamlit应用界面
"""
import streamlit as st
import os
import sys
import json
from datetime import datetime

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.agent.langgraph_agent import GrassrootsAdvisorAgent
from src.rag.chains import ConversationalRAGChain
from src.knowledge_base.vector_store import VectorStoreManager, build_knowledge_base
from src.knowledge_base.loader import create_sample_cases
from src.governance_agent import GrassrootsGovernanceAgent, ProblemType
from src.utils.logger import logger
from config import config

# 页面配置
st.set_page_config(
    page_title="基层工作智能辅助Agent",
    page_icon="🏢",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 自定义CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .sub-header {
        font-size: 1.2rem;
        color: #666;
        text-align: center;
        margin-bottom: 2rem;
    }
    .case-box {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
        border-left: 4px solid #1f77b4;
    }
    .solution-box {
        background-color: #e8f5e8;
        padding: 1.5rem;
        border-radius: 0.5rem;
        margin: 1rem 0;
        border-left: 4px solid #28a745;
    }
    .warning-box {
        background-color: #fff3cd;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
        border-left: 4px solid #ffc107;
    }
    .error-box {
        background-color: #f8d7da;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
        border-left: 4px solid #dc3545;
    }
</style>
""", unsafe_allow_html=True)

@st.cache_resource
def load_agent(use_rules: bool = True):
    """加载Agent（使用缓存避免重复初始化）"""
    try:
        return GrassrootsAdvisorAgent(use_rules=use_rules)
    except Exception as e:
        st.error(f"Agent初始化失败: {e}")
        return None

@st.cache_resource
def load_conversational_rag():
    """加载对话式RAG链"""
    try:
        return ConversationalRAGChain()
    except Exception as e:
        st.error(f"对话式RAG初始化失败: {e}")
        return None

@st.cache_resource
def load_governance_agent():
    """加载治理Agent（使用缓存避免重复初始化）"""
    try:
        return GrassrootsGovernanceAgent()
    except Exception as e:
        st.error(f"治理Agent初始化失败: {e}")
        return None

def init_session_state():
    """初始化会话状态"""
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []
    
    if "current_solution" not in st.session_state:
        st.session_state.current_solution = None
    
    if "knowledge_base_status" not in st.session_state:
        st.session_state.knowledge_base_status = "未检查"

def check_knowledge_base():
    """检查知识库状态"""
    try:
        vector_manager = VectorStoreManager()
        info = vector_manager.get_collection_info()
        
        if info.get("document_count", 0) > 0:
            st.session_state.knowledge_base_status = f"已就绪 ({info['document_count']} 个文档)"
            return True
        else:
            st.session_state.knowledge_base_status = "空"
            return False
    except Exception as e:
        st.session_state.knowledge_base_status = f"错误: {e}"
        return False

def build_knowledge_base_ui():
    """构建知识库UI"""
    st.subheader("📚 知识库管理")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("🔍 检查知识库状态"):
            with st.spinner("检查中..."):
                check_knowledge_base()
            st.rerun()
    
    with col2:
        if st.button("🏗️ 构建知识库"):
            with st.spinner("构建中..."):
                # 确保示例案例存在
                sample_path = "./data/knowledge_base/sample_cases.json"
                if not os.path.exists(sample_path):
                    os.makedirs(os.path.dirname(sample_path), exist_ok=True)
                    create_sample_cases(sample_path)
                
                # 构建知识库
                success = build_knowledge_base()
                if success:
                    st.success("✅ 知识库构建成功！")
                    check_knowledge_base()
                else:
                    st.error("❌ 知识库构建失败")
            st.rerun()
    
    with col3:
        if st.button("🗑️ 重置知识库"):
            with st.spinner("重置中..."):
                try:
                    vector_manager = VectorStoreManager()
                    vector_manager.delete_collection()
                    st.success("✅ 知识库已重置")
                    check_knowledge_base()
                except Exception as e:
                    st.error(f"❌ 重置失败: {e}")
            st.rerun()
    
    # 显示状态
    if st.session_state.knowledge_base_status:
        if "已就绪" in st.session_state.knowledge_base_status:
            st.success(f"知识库状态: {st.session_state.knowledge_base_status}")
        elif "空" in st.session_state.knowledge_base_status:
            st.warning(f"知识库状态: {st.session_state.knowledge_base_status}")
        else:
            st.error(f"知识库状态: {st.session_state.knowledge_base_status}")

def display_solution_analysis(result):
    """显示解决方案分析"""
    if not result.get("success", False):
        st.markdown(f'<div class="error-box">❌ {result.get("error", "未知错误")}</div>', 
                   unsafe_allow_html=True)
        return
    
    # 显示检索的案例
    retrieved_cases = result.get("retrieved_cases", [])
    if retrieved_cases:
        st.subheader("📋 相关案例")
        for i, case in enumerate(retrieved_cases[:3], 1):
            with st.expander(f"案例 {i}: {case.get('title', '未知标题')}"):
                st.markdown(f"**类别:** {case.get('category', '未知')}")
                st.markdown(f"**内容:** {case.get('content', '无内容')}")
    
    # 显示分析结果
    analysis_result = result.get("analysis_result", {})
    if analysis_result.get("analyses"):
        st.subheader("🔍 案例分析")
        for analysis in analysis_result["analyses"]:
            case_title = analysis.get("case_title", "未知案例")
            analysis_data = analysis.get("analysis", {})
            
            with st.expander(f"分析: {case_title}"):
                if isinstance(analysis_data, dict):
                    for key, value in analysis_data.items():
                        st.markdown(f"**{key}:** {value}")
                else:
                    st.markdown(analysis_data)
    
    # 显示最终解决方案
    final_solution = result.get("final_solution", "")
    if final_solution:
        st.subheader("💡 推荐解决方案")
        st.markdown(f'<div class="solution-box">{final_solution}</div>', 
                   unsafe_allow_html=True)

def main():
    """主应用"""
    init_session_state()
    
    # 应用标题
    st.markdown('<div class="main-header">🏢 基层工作智能辅助Agent</div>', 
                unsafe_allow_html=True)
    st.markdown('<div class="sub-header">基于成功案例的智能化工作指导系统</div>', 
                unsafe_allow_html=True)
    
    # 侧边栏
    with st.sidebar:
        st.header("⚙️ 系统设置")
        
        # API Key设置
        api_key = st.text_input(
            "OpenAI API Key", 
            value=config.DASHSCOPE_API_KEY,
            type="password",
            help="请输入您的OpenAI API Key"
        )
        
        if api_key != config.DASHSCOPE_API_KEY:
            os.environ["OPENAI_API_KEY"] = api_key
            config.DASHSCOPE_API_KEY = api_key
        
        st.divider()
        
        # 模式选择
        mode = st.selectbox(
            "选择工作模式",
            ["简单问答", "深度分析", "对话交流", "治理问题解决", "批量问题处理"],
            help="选择不同的工作模式"
        )
        
        # 法规感知开关
        use_rules = st.checkbox(
            "启用法规感知",
            value=True,
            help="启用后将结合法规政策提供合规建议"
        )
        
        st.divider()
        
        # 知识库管理
        build_knowledge_base_ui()
        
        st.divider()
        
        # 系统信息
        st.subheader("📊 系统信息")
        st.info(f"""
        - 配置状态: {'✅' if config.DASHSCOPE_API_KEY else '❌'}
        - 知识库: {st.session_state.knowledge_base_status}
        - 对话历史: {len(st.session_state.chat_history)} 条
        """)
    
    # 主界面
    if not config.DASHSCOPE_API_KEY:
        st.warning("⚠️ 请在侧边栏设置OpenAI API Key")
        return
    
    # 检查知识库状态
    if st.session_state.knowledge_base_status == "未检查":
        check_knowledge_base()
    
    # 根据模式显示不同界面
    if mode == "简单问答":
        simple_qa_mode()
    elif mode == "深度分析":
        deep_analysis_mode()
    elif mode == "治理问题解决":
        governance_mode()
    elif mode == "批量问题处理":
        batch_governance_mode()
    else:
        conversation_mode()

def simple_qa_mode():
    """简单问答模式"""
    st.header("💬 简单问答模式")
    st.info("直接基于知识库案例进行快速问答")
    
    # 获取法规感知设置
    use_rules = st.sidebar.checkbox(
        "启用法规感知",
        value=True,
        help="启用后将结合法规政策提供合规建议",
        key="simple_qa_use_rules"
    )
    
    # 输入问题
    question = st.text_area(
        "请输入您的问题:",
        placeholder="例如：如何处理邻里纠纷？",
        height=100
    )
    
    if st.button("🚀 获取建议", use_container_width=True):
        if question.strip():
            with st.spinner("正在分析问题并生成建议..."):
                agent = load_agent(use_rules=use_rules)
                if agent:
                    answer = agent.get_simple_answer(question)
                    
                    st.subheader("💡 建议方案")
                    # st.markdown(f'<div class="solution-box">{answer}</div>', 
                    #            unsafe_allow_html=True)
                    with st.chat_message("assistant"):
                        st.write_stream(agent.rag_chain.stream(question)) 
                    
                    # 显示相关案例
                    relevant_cases = agent.rag_chain.get_relevant_cases(question, k=3)
                    if relevant_cases:
                        st.subheader("📚 参考案例")
                        for i, case in enumerate(relevant_cases, 1):
                            with st.expander(f"案例 {i}: {case.metadata.get('title', '未知')}"):
                                st.markdown(f"**类别:** {case.metadata.get('category', '未知')}")
                                st.markdown(f"**内容:** {case.page_content}")
        else:
            st.warning("请输入问题")

def deep_analysis_mode():
    """深度分析模式"""
    st.header("🔬 深度分析模式")
    st.info("使用LangGraph进行多步骤分析，提供详细的解决方案")
    
    # 获取法规感知设置
    use_rules = st.sidebar.checkbox(
        "启用法规感知",
        value=True,
        help="启用后将结合法规政策提供合规建议",
        key="deep_analysis_use_rules"
    )
    
    # 输入问题
    question = st.text_area(
        "请详细描述您遇到的问题:",
        placeholder="例如：我们社区老人较多，如何更好地开展政策宣传工作？",
        height=120
    )
    
    # 高级设置
    with st.expander("🛠️ 高级设置"):
        max_iterations = st.slider("最大迭代次数", 1, 3, 1)
        st.info("增加迭代次数可以获得更精细的方案，但会消耗更多时间")
    
    if st.button("🔍 深度分析", use_container_width=True):
        if question.strip():
            with st.spinner("正在进行深度分析..."):
                agent = load_agent(use_rules=use_rules)
                if agent:
                    result = agent.solve_problem(question, max_iterations=max_iterations)
                    
                    # 显示分析结果
                    display_solution_analysis(result)
                    
                    # 保存结果到会话状态
                    st.session_state.current_solution = result
        else:
            st.warning("请输入问题")

def conversation_mode():
    """对话交流模式"""
    st.header("💬 对话交流模式")
    st.info("支持多轮对话，可以持续深入探讨问题")
    
    # 显示对话历史
    if st.session_state.chat_history:
        st.subheader("📜 对话历史")
        for i, chat in enumerate(st.session_state.chat_history):
            with st.expander(f"对话 {i+1}: {chat['question'][:50]}..."):
                st.markdown(f"**问题:** {chat['question']}")
                st.markdown(f"**回答:** {chat['answer']}")
    
    # 输入新问题
    question = st.text_input(
        "请输入您的问题:",
        placeholder="您可以提问或者针对之前的回答进行追问...",
        key="conversation_input"
    )
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("💬 发送", use_container_width=True):
            if question.strip():
                with st.spinner("正在生成回答..."):
                    conv_rag = load_conversational_rag()
                    if conv_rag:
                        with st.chat_message("assistant"):
                            st.write_stream(conv_rag.stream_chat(question))
                        
                        # 添加到对话历史（由流式方法内部更新，这里只读取最新历史以显示简短摘要）
                        if st.session_state.get("chat_history") is None:
                            st.session_state.chat_history = []
                        st.session_state.chat_history.append({
                            "question": question,
                            "answer": "(以上为流式输出)",
                            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        })
                        
                        # 清空输入框
                        st.rerun()
# 清空输入框
                        st.rerun()
            else:
                st.warning("请输入问题")
    
    with col2:
        if st.button("🗑️ 清除历史", use_container_width=True):
            st.session_state.chat_history = []
            conv_rag = load_conversational_rag()
            if conv_rag:
                conv_rag.clear_history()
            st.success("对话历史已清除")
            st.rerun()

def governance_mode():
    """治理问题解决模式"""
    st.header("🏛️ 治理问题解决模式")
    st.info("基于案例驱动的智能治理解决方案生成系统")
    
    # 问题基本信息
    col1, col2 = st.columns(2)
    
    with col1:
        problem_description = st.text_area(
            "问题描述 *",
            placeholder="请详细描述遇到的治理问题...",
            height=120,
            help="请尽可能详细地描述问题的具体情况"
        )
        
        location = st.text_input(
            "地区位置 *",
            placeholder="例如：北京市朝阳区某社区",
            help="问题发生的具体地区"
        )
        
        urgency_level = st.slider(
            "紧急程度",
            min_value=1,
            max_value=5,
            value=3,
            help="1-最低，5-最高"
        )
    
    with col2:
        stakeholders = st.text_area(
            "利益相关方",
            placeholder="例如：社区居民、物业公司、街道办事处",
            height=80,
            help="涉及的相关方，每行一个"
        )
        
        constraints = st.text_area(
            "约束条件",
            placeholder="例如：预算有限、时间紧迫、法规限制",
            height=80,
            help="解决问题时需要考虑的限制条件"
        )
        
        expected_outcome = st.text_input(
            "期望结果",
            placeholder="例如：彻底解决纠纷，恢复社区和谐",
            help="希望达到的目标"
        )
    
    # 可选信息
    with st.expander("📋 可选信息"):
        col3, col4 = st.columns(2)
        
        with col3:
            timeline = st.text_input(
                "期望时间线",
                placeholder="例如：1个月内解决",
                help="希望在多长时间内解决问题"
            )
        
        with col4:
            budget_range = st.text_input(
                "预算范围",
                placeholder="例如：5-10万元",
                help="可用于解决问题的预算范围"
            )
    
    # 生成解决方案
    if st.button("🚀 生成解决方案", use_container_width=True):
        if problem_description.strip() and location.strip():
            with st.spinner("正在分析问题并生成解决方案..."):
                governance_agent = load_governance_agent()
                if governance_agent:
                    # 处理输入数据
                    stakeholders_list = [s.strip() for s in stakeholders.split('\n') if s.strip()] if stakeholders else []
                    constraints_list = [c.strip() for c in constraints.split('\n') if c.strip()] if constraints else []
                    
                    result = governance_agent.solve_governance_problem(
                        problem_description=problem_description,
                        location=location,
                        urgency_level=urgency_level,
                        stakeholders=stakeholders_list,
                        constraints=constraints_list,
                        expected_outcome=expected_outcome,
                        timeline=timeline if timeline else None,
                        budget_range=budget_range if budget_range else None
                    )
                    
                    if "error" not in result:
                        display_governance_solution(result)
                    else:
                        st.error(f"❌ 生成解决方案失败: {result['error']}")
        else:
            st.warning("请填写问题描述和地区位置")

def batch_governance_mode():
    """批量问题处理模式"""
    st.header("📊 批量问题处理模式")
    st.info("一次性处理多个治理问题，提高工作效率")
    
    # 文件上传
    uploaded_file = st.file_uploader(
        "上传问题列表文件",
        type=['json', 'csv'],
        help="支持JSON和CSV格式文件"
    )
    
    # 手动输入
    st.subheader("或手动输入问题")
    
    if "batch_problems" not in st.session_state:
        st.session_state.batch_problems = []
    
    # 添加问题表单
    with st.expander("➕ 添加新问题"):
        col1, col2 = st.columns(2)
        
        with col1:
            new_description = st.text_area("问题描述", key="new_desc")
            new_location = st.text_input("地区位置", key="new_loc")
            new_urgency = st.slider("紧急程度", 1, 5, 3, key="new_urgency")
        
        with col2:
            new_stakeholders = st.text_area("利益相关方", key="new_stakeholders")
            new_constraints = st.text_area("约束条件", key="new_constraints")
            new_outcome = st.text_input("期望结果", key="new_outcome")
        
        if st.button("添加到批处理列表"):
            if new_description and new_location:
                problem = {
                    "description": new_description,
                    "location": new_location,
                    "urgency_level": new_urgency,
                    "stakeholders": [s.strip() for s in new_stakeholders.split('\n') if s.strip()],
                    "constraints": [c.strip() for c in new_constraints.split('\n') if c.strip()],
                    "expected_outcome": new_outcome
                }
                st.session_state.batch_problems.append(problem)
                st.success("问题已添加到批处理列表")
                st.rerun()
            else:
                st.warning("请填写问题描述和地区位置")
    
    # 显示当前问题列表
    if st.session_state.batch_problems:
        st.subheader(f"📋 待处理问题列表 ({len(st.session_state.batch_problems)} 个)")
        
        for i, problem in enumerate(st.session_state.batch_problems):
            with st.expander(f"问题 {i+1}: {problem['description'][:50]}..."):
                st.json(problem)
                if st.button(f"删除问题 {i+1}", key=f"del_{i}"):
                    st.session_state.batch_problems.pop(i)
                    st.rerun()
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("🚀 批量处理", use_container_width=True):
                with st.spinner("正在批量处理问题..."):
                    governance_agent = load_governance_agent()
                    if governance_agent:
                        results = governance_agent.batch_solve_problems(st.session_state.batch_problems)
                        
                        st.subheader("📊 批处理结果")
                        
                        success_count = sum(1 for r in results if "error" not in r)
                        st.metric("成功处理", f"{success_count}/{len(results)}")
                        
                        for i, result in enumerate(results):
                            with st.expander(f"结果 {i+1}: {'✅ 成功' if 'error' not in result else '❌ 失败'}"):
                                if "error" not in result:
                                    display_governance_solution(result, compact=True)
                                else:
                                    st.error(f"处理失败: {result['error']}")
        
        with col2:
            if st.button("🗑️ 清空列表", use_container_width=True):
                st.session_state.batch_problems = []
                st.success("问题列表已清空")
                st.rerun()
    
    else:
        st.info("暂无待处理问题，请添加问题或上传文件")

def display_governance_solution(result, compact=False):
    """显示治理解决方案"""
    if "error" in result:
        st.error(f"❌ {result['error']}")
        return
    
    # 问题信息
    problem = result.get("problem", {})
    if not compact:
        st.subheader("📋 问题信息")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("问题类型", problem.get("problem_type", "未知"))
            st.metric("紧急程度", f"{problem.get('urgency_level', 0)}/5")
        
        with col2:
            st.metric("地区", problem.get("location", "未知"))
            st.metric("利益相关方", len(problem.get("stakeholders", [])))
        
        with col3:
            st.metric("约束条件", len(problem.get("constraints", [])))
    
    # 解决方案
    solution_plan = result.get("solution_plan", {})
    if solution_plan:
        st.subheader("💡 解决方案")
        
        # 解决步骤
        steps = solution_plan.get("steps", [])
        if steps:
            st.markdown("**实施步骤:**")
            for i, step in enumerate(steps, 1):
                if isinstance(step, dict):
                    step_title = step.get("title", f"步骤 {i}")
                    step_desc = step.get("description", "无描述")
                    st.markdown(f"{i}. **{step_title}**: {step_desc}")
                else:
                    st.markdown(f"{i}. {step}")
        
        # 时间线
        timeline = solution_plan.get("timeline", {})
        if timeline and not compact:
            st.markdown("**时间安排:**")
            for phase, time in timeline.items():
                st.markdown(f"- {phase}: {time}")
        
        # 资源需求
        resources = solution_plan.get("resource_requirements", {})
        if resources and not compact:
            st.markdown("**资源需求:**")
            for resource_type, requirement in resources.items():
                st.markdown(f"- {resource_type}: {requirement}")
    
    # 参考案例
    case_refs = result.get("case_references", [])
    if case_refs and not compact:
        st.subheader("📚 参考案例")
        for i, case in enumerate(case_refs[:3], 1):
            with st.expander(f"案例 {i}: {case.get('title', '未知标题')}"):
                st.markdown(f"**相似度**: {case.get('similarity_score', 0):.2f}")
                st.markdown(f"**问题类型**: {case.get('problem_type', '未知')}")
                
                key_measures = case.get("key_measures", [])
                if key_measures:
                    st.markdown("**关键措施**:")
                    for measure in key_measures:
                        st.markdown(f"- {measure}")
    
    # 政策参考
    policy_refs = result.get("policy_references", [])
    if policy_refs and not compact:
        st.subheader("📜 政策参考")
        for i, policy in enumerate(policy_refs[:3], 1):
            with st.expander(f"政策 {i}: {policy.get('title', '未知标题')}"):
                st.markdown(f"**相关度**: {policy.get('relevance_score', 0):.2f}")
                st.markdown(f"**行政层级**: {policy.get('admin_level', '未知')}")
                
                key_provisions = policy.get("key_provisions", [])
                if key_provisions:
                    st.markdown("**关键条款**:")
                    for provision in key_provisions:
                        st.markdown(f"- {provision}")
    
    # 评估结果
    evaluation = result.get("evaluation", {})
    if evaluation and not compact:
        st.subheader("📊 方案评估")
        
        overall_score = evaluation.get("overall_score", 0)
        st.metric("综合评分", f"{overall_score:.2f}/5.0")
        
        # 各维度评分
        dimensions = evaluation.get("dimension_scores", {})
        if dimensions:
            cols = st.columns(len(dimensions))
            for i, (dim, score) in enumerate(dimensions.items()):
                with cols[i]:
                    st.metric(dim, f"{score:.2f}")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        st.error(f"应用运行时出现错误: {e}")
        logger.error(f"Streamlit应用错误: {e}") 