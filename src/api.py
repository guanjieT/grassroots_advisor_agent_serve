"""
基层工作智能辅助Agent - FastAPI接口
"""
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
import asyncio
import uvicorn
from datetime import datetime

from src.agent.langgraph_agent import GrassrootsAdvisorAgent
from src.rag.chains import RAGChain, ConversationalRAGChain
from src.knowledge_base.vector_store import VectorStoreManager, build_knowledge_base
from src.governance_agent import GrassrootsGovernanceAgent, ProblemType
from src.utils.logger import logger
from config import config

# 创建FastAPI应用
app = FastAPI(
    title="基层工作智能辅助Agent API",
    description="基于LangChain、LangGraph和LangSmith的基层工作智能辅助系统",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# 添加CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 请求模型
class QuestionRequest(BaseModel):
    question: str = Field(..., description="用户问题", min_length=1, max_length=1000)
    max_iterations: Optional[int] = Field(1, description="最大迭代次数", ge=1, le=3)

class ChatRequest(BaseModel):
    question: str = Field(..., description="用户问题", min_length=1, max_length=1000)
    session_id: Optional[str] = Field(None, description="会话ID")

class GovernanceProblemRequest(BaseModel):
    problem_description: str = Field(..., description="问题描述", min_length=1, max_length=2000)
    location: str = Field(..., description="地区位置", min_length=1, max_length=100)
    urgency_level: Optional[int] = Field(3, description="紧急程度 (1-5)", ge=1, le=5)
    stakeholders: Optional[List[str]] = Field([], description="利益相关方列表")
    constraints: Optional[List[str]] = Field([], description="约束条件列表")
    expected_outcome: Optional[str] = Field("", description="期望结果")
    timeline: Optional[str] = Field(None, description="期望时间线")
    budget_range: Optional[str] = Field(None, description="预算范围")

class BatchProblemsRequest(BaseModel):
    problems: List[Dict[str, Any]] = Field(..., description="批量问题列表")

class CompareSolutionsRequest(BaseModel):
    problem_description: str = Field(..., description="问题描述", min_length=1, max_length=2000)
    location: str = Field(..., description="地区位置", min_length=1, max_length=100)
    alternative_approaches: Optional[List[str]] = Field([], description="替代方案列表")

# 响应模型
class SimpleAnswerResponse(BaseModel):
    question: str
    answer: str
    timestamp: str
    success: bool = True

class DeepAnalysisResponse(BaseModel):
    question: str
    retrieved_cases: List[Dict[str, Any]]
    analysis_result: Dict[str, Any]
    solution_draft: str
    final_solution: str
    iteration_count: int
    timestamp: str
    success: bool = True

class ChatResponse(BaseModel):
    question: str
    answer: str
    session_id: str
    timestamp: str
    success: bool = True

class GovernanceSolutionResponse(BaseModel):
    problem: Dict[str, Any]
    solution_plan: Dict[str, Any]
    case_references: List[Dict[str, Any]]
    policy_references: List[Dict[str, Any]]
    evaluation: Dict[str, Any]
    compliance_check: Dict[str, Any]
    generation_metadata: Dict[str, Any]
    success: bool = True

class SystemStatusResponse(BaseModel):
    system_initialized: bool
    subsystems: Dict[str, Any]
    statistics: Dict[str, Any]
    success: bool = True

# 全局变量存储Agent实例
_agent = None
_governance_agent = None
_rag_chain = None
_conversation_sessions = {}

async def get_agent():
    """获取Agent实例（单例模式）"""
    global _agent
    if _agent is None:
        try:
            _agent = GrassrootsAdvisorAgent()
            logger.info("Agent实例创建成功")
        except Exception as e:
            logger.error(f"Agent创建失败: {e}")
            raise HTTPException(status_code=500, detail=f"Agent初始化失败: {str(e)}")
    return _agent

async def get_governance_agent():
    """获取治理Agent实例（单例模式）"""
    global _governance_agent
    if _governance_agent is None:
        try:
            _governance_agent = GrassrootsGovernanceAgent()
            logger.info("治理Agent实例创建成功")
        except Exception as e:
            logger.error(f"治理Agent创建失败: {e}")
            raise HTTPException(status_code=500, detail=f"治理Agent初始化失败: {str(e)}")
    return _governance_agent

def get_conversation_session(session_id: str):
    """获取对话会话"""
    global _conversation_sessions
    if session_id not in _conversation_sessions:
        try:
            _conversation_sessions[session_id] = ConversationalRAGChain()
            logger.info(f"创建新对话会话: {session_id}")
        except Exception as e:
            logger.error(f"对话会话创建失败: {e}")
            raise HTTPException(status_code=500, detail=f"对话会话初始化失败: {str(e)}")
    return _conversation_sessions[session_id]

# API路由
@app.get("/", summary="健康检查")
async def health_check():
    """健康检查接口"""
    return {
        "status": "healthy",
        "service": "基层工作智能辅助Agent",
        "version": "1.0.0",
        "timestamp": datetime.now().isoformat()
    }

@app.post("/api/simple-answer", 
          response_model=SimpleAnswerResponse,
          summary="简单问答",
          description="使用RAG链进行简单快速的问答")
async def simple_answer(request: QuestionRequest):
    """简单问答接口"""
    try:
        logger.info(f"简单问答请求: {request.question}")
        
        agent = await get_agent()
        answer = agent.get_simple_answer(request.question)
        
        response = SimpleAnswerResponse(
            question=request.question,
            answer=answer,
            timestamp=datetime.now().isoformat()
        )
        
        logger.info("简单问答完成")
        return response
        
    except Exception as e:
        logger.error(f"简单问答失败: {e}")
        raise HTTPException(status_code=500, detail=f"简单问答处理失败: {str(e)}")

@app.post("/api/deep-analysis",
          response_model=DeepAnalysisResponse,
          summary="深度分析",
          description="使用LangGraph进行深度分析和多步骤推理")
async def deep_analysis(request: QuestionRequest):
    """深度分析接口"""
    try:
        logger.info(f"深度分析请求: {request.question}")
        
        agent = await get_agent()
        result = agent.solve_problem(request.question, max_iterations=request.max_iterations)
        
        if not result.get("success", False):
            raise HTTPException(status_code=500, detail=result.get("error", "深度分析失败"))
        
        response = DeepAnalysisResponse(
            question=result["question"],
            retrieved_cases=result.get("retrieved_cases", []),
            analysis_result=result.get("analysis_result", {}),
            solution_draft=result.get("solution_draft", ""),
            final_solution=result.get("final_solution", ""),
            iteration_count=result.get("iteration_count", 0),
            timestamp=datetime.now().isoformat()
        )
        
        logger.info("深度分析完成")
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"深度分析失败: {e}")
        raise HTTPException(status_code=500, detail=f"深度分析处理失败: {str(e)}")

@app.post("/api/chat",
          response_model=ChatResponse,
          summary="对话聊天",
          description="支持多轮对话的智能问答")
async def chat(request: ChatRequest):
    """对话聊天接口"""
    try:
        # 生成会话ID（如果没有提供）
        session_id = request.session_id or f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        logger.info(f"对话请求 [{session_id}]: {request.question}")
        
        # 获取对话会话
        conv_rag = get_conversation_session(session_id)
        
        # 生成回答
        answer = conv_rag.chat(request.question)
        
        response = ChatResponse(
            question=request.question,
            answer=answer,
            session_id=session_id,
            timestamp=datetime.now().isoformat()
        )
        
        logger.info(f"对话完成 [{session_id}]")
        return response
        
    except Exception as e:
        logger.error(f"对话处理失败: {e}")
        raise HTTPException(status_code=500, detail=f"对话处理失败: {str(e)}")

@app.post("/api/governance/solve-problem",
          response_model=GovernanceSolutionResponse,
          summary="治理问题解决",
          description="使用案例驱动模式解决基层治理问题")
async def solve_governance_problem(request: GovernanceProblemRequest):
    """治理问题解决接口"""
    try:
        logger.info(f"治理问题解决请求: {request.problem_description[:50]}...")
        
        governance_agent = await get_governance_agent()
        result = governance_agent.solve_governance_problem(
            problem_description=request.problem_description,
            location=request.location,
            urgency_level=request.urgency_level,
            stakeholders=request.stakeholders,
            constraints=request.constraints,
            expected_outcome=request.expected_outcome,
            timeline=request.timeline,
            budget_range=request.budget_range
        )
        
        if "error" in result:
            raise HTTPException(status_code=500, detail=result["error"])
        
        response = GovernanceSolutionResponse(**result)
        logger.info("治理问题解决完成")
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"治理问题解决失败: {e}")
        raise HTTPException(status_code=500, detail=f"治理问题解决失败: {str(e)}")

@app.post("/api/governance/batch-solve",
          summary="批量治理问题解决",
          description="批量处理多个治理问题")
async def batch_solve_problems(request: BatchProblemsRequest):
    """批量治理问题解决接口"""
    try:
        logger.info(f"批量治理问题解决请求: {len(request.problems)} 个问题")
        
        governance_agent = await get_governance_agent()
        results = governance_agent.batch_solve_problems(request.problems)
        
        logger.info("批量治理问题解决完成")
        return {
            "results": results,
            "total_problems": len(request.problems),
            "timestamp": datetime.now().isoformat(),
            "success": True
        }
        
    except Exception as e:
        logger.error(f"批量治理问题解决失败: {e}")
        raise HTTPException(status_code=500, detail=f"批量治理问题解决失败: {str(e)}")

@app.post("/api/governance/compare-solutions",
          summary="比较解决方案",
          description="比较不同治理问题解决方案")
async def compare_solutions(request: CompareSolutionsRequest):
    """比较解决方案接口"""
    try:
        logger.info(f"比较解决方案请求: {request.problem_description[:50]}...")
        
        governance_agent = await get_governance_agent()
        result = governance_agent.compare_solutions(
            problem_description=request.problem_description,
            location=request.location,
            alternative_approaches=request.alternative_approaches
        )
        
        if "error" in result:
            raise HTTPException(status_code=500, detail=result["error"])
        
        logger.info("比较解决方案完成")
        return {
            **result,
            "timestamp": datetime.now().isoformat(),
            "success": True
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"比较解决方案失败: {e}")
        raise HTTPException(status_code=500, detail=f"比较解决方案失败: {str(e)}")

@app.get("/api/governance/system-status",
         response_model=SystemStatusResponse,
         summary="系统状态",
         description="获取治理系统状态信息")
async def get_system_status():
    """获取系统状态接口"""
    try:
        logger.info("获取系统状态请求")
        
        governance_agent = await get_governance_agent()
        status = governance_agent.get_system_status()
        
        if "error" in status:
            raise HTTPException(status_code=500, detail=status["error"])
        
        response = SystemStatusResponse(**status)
        logger.info("获取系统状态完成")
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取系统状态失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取系统状态失败: {str(e)}")

@app.get("/api/governance/problem-types",
         summary="问题类型列表",
         description="获取支持的治理问题类型")
async def get_problem_types():
    """获取问题类型列表"""
    try:
        problem_types = [
            {"value": ptype.value, "name": ptype.name} 
            for ptype in ProblemType
        ]
        
        return {
            "problem_types": problem_types,
            "timestamp": datetime.now().isoformat(),
            "success": True
        }
        
    except Exception as e:
        logger.error(f"获取问题类型失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取问题类型失败: {str(e)}")

if __name__ == "__main__":
    # 运行FastAPI应用
    uvicorn.run(
        "api:app",
        host="0.0.0.0",
        port=8000,
        reload=config.APP_DEBUG,
        log_level=config.LOG_LEVEL.lower()
    ) 

@app.post("/api/stream/simple-answer", summary="简单问答（流式）", description="流式输出的简单问答，返回text/plain流")
async def simple_answer_stream(request: QuestionRequest):
    try:
        agent = await get_agent()
        chain = agent.rag_chain
        def gen():
            for chunk in chain.stream(request.question):
                yield str(chunk)
        return StreamingResponse(gen(), media_type="text/plain")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"简单问答流式失败: {e}")

@app.post("/api/stream/chat", summary="对话聊天（流式）", description="流式输出的多轮对话，返回text/plain流")
async def chat_stream(request: ChatRequest):
    try:
        session_id = request.session_id or f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        conv_rag = get_conversation_session(session_id)
        def gen():
            for chunk in conv_rag.stream_chat(request.question):
                yield str(chunk)
        return StreamingResponse(gen(), media_type="text/plain")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"对话流式失败: {e}")
