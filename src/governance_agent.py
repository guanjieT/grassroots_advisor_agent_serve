"""
基层治理辅助Agent系统 - 主系统
以案例驱动模式为核心的智能治理解决方案生成系统
"""
import os
import sys
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
from dataclasses import dataclass
from enum import Enum

# 添加项目根目录到路径
project_root = os.path.dirname(os.path.abspath(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from config import config
from src.utils.logger import logger

class ProblemType(Enum):
    """问题类型枚举"""
    NEIGHBOR_DISPUTE = "邻里纠纷"
    COMMUNITY_SERVICE = "社区服务"
    ENVIRONMENT_GOVERNANCE = "环境治理"
    SAFETY_MANAGEMENT = "安全管理"
    POLICY_PROMOTION = "政策宣传"
    ELDERLY_SERVICE = "养老服务"
    PARKING_MANAGEMENT = "停车管理"
    DIGITAL_DIVIDE = "数字鸿沟"
    OTHER = "其他"

class AdminLevel(Enum):
    """行政层级枚举"""
    CENTRAL = "中央"
    PROVINCIAL = "省级"
    MUNICIPAL = "市级"
    COUNTY = "区县"
    STREET = "街道社区"

@dataclass
class GovernanceProblem:
    """治理问题数据结构"""
    description: str
    location: str
    problem_type: ProblemType
    urgency_level: int  # 1-5级，5最紧急
    stakeholders: List[str]
    constraints: List[str]
    expected_outcome: str
    timeline: Optional[str] = None
    budget_range: Optional[str] = None

@dataclass
class CaseReference:
    """案例参考数据结构"""
    case_id: str
    title: str
    problem_type: str
    similarity_score: float
    key_measures: List[str]
    success_factors: List[str]
    applicable_conditions: List[str]
    source: str

@dataclass
class PolicyReference:
    """政策参考数据结构"""
    policy_id: str
    title: str
    admin_level: str
    relevance_score: float
    key_provisions: List[str]
    compliance_requirements: List[str]
    implementation_guidance: List[str]
    source: str

@dataclass
class SolutionPlan:
    """解决方案数据结构"""
    problem: GovernanceProblem
    case_references: List[CaseReference]
    policy_references: List[PolicyReference]
    solution_steps: List[Dict[str, Any]]
    risk_assessment: Dict[str, Any]
    resource_requirements: Dict[str, Any]
    success_metrics: List[str]
    timeline: Dict[str, str]
    local_adaptations: List[str]
    generated_at: datetime

class GrassrootsGovernanceAgent:
    """基层治理辅助Agent主系统"""
    
    def __init__(self):
        """初始化系统"""
        logger.info("初始化基层治理辅助Agent系统...")
        
        # 初始化各个子系统
        self.case_engine = None
        self.policy_engine = None
        self.solution_generator = None
        self.evaluation_engine = None
        
        # 系统状态
        self.is_initialized = False
        
        # 初始化子系统
        self._initialize_subsystems()
        
        logger.info("基层治理辅助Agent系统初始化完成")
    
    def _initialize_subsystems(self):
        """初始化各个子系统"""
        try:
            # 延迟导入避免循环依赖
            from src.core.case_engine import CaseEngine
            from src.core.policy_engine import PolicyEngine
            from src.core.solution_generator import SolutionGenerator
            from src.core.evaluation_engine import EvaluationEngine
            
            self.case_engine = CaseEngine()
            self.policy_engine = PolicyEngine()
            self.solution_generator = SolutionGenerator()
            self.evaluation_engine = EvaluationEngine()
            
            self.is_initialized = True
            logger.info("所有子系统初始化完成")
            
        except Exception as e:
            logger.error(f"子系统初始化失败: {e}")
            raise
    
    def solve_governance_problem(
        self,
        problem_description: str,
        location: str,
        urgency_level: int = 3,
        stakeholders: List[str] = None,
        constraints: List[str] = None,
        expected_outcome: str = "",
        timeline: str = None,
        budget_range: str = None
    ) -> Dict[str, Any]:
        """
        解决基层治理问题的主要接口
        
        Args:
            problem_description: 问题描述
            location: 地区位置
            urgency_level: 紧急程度 (1-5)
            stakeholders: 利益相关方列表
            constraints: 约束条件列表
            expected_outcome: 期望结果
            timeline: 期望时间线
            budget_range: 预算范围
            
        Returns:
            完整的解决方案和评估结果
        """
        try:
            if not self.is_initialized:
                raise Exception("系统未初始化")
            
            logger.info(f"开始处理治理问题: {problem_description[:50]}...")
            
            # 1. 构建问题对象
            problem = GovernanceProblem(
                description=problem_description,
                location=location,
                problem_type=self._infer_problem_type(problem_description),
                urgency_level=urgency_level,
                stakeholders=stakeholders or [],
                constraints=constraints or [],
                expected_outcome=expected_outcome,
                timeline=timeline,
                budget_range=budget_range
            )
            
            # 2. 查找相似案例
            logger.info("查找相似成功案例...")
            similar_cases = self.case_engine.find_similar_cases(
                problem_description=problem_description,
                problem_type=problem.problem_type.value,
                k=5
            )
            
            # 3. 查找相关政策
            logger.info("查找相关政策法规...")
            # 暂时不过滤层级，让所有政策都能被检索到
            relevant_policies = self.policy_engine.find_relevant_policies(
                problem_description=problem_description,
                location=location,
                admin_levels=None,  # 暂时不过滤层级
                k=5
            )
            
            # 4. 生成解决方案
            logger.info("生成解决方案...")
            solution_plan = self.solution_generator.generate_solution(
                problem=problem,
                case_references=similar_cases,
                policy_references=relevant_policies
            )
            
            # 5. 评估解决方案
            logger.info("评估解决方案质量...")
            evaluation_result = self.evaluation_engine.evaluate_solution(solution_plan)
            
            # 6. 检查政策合规性
            logger.info("检查政策合规性...")
            compliance_check = self.policy_engine.check_policy_compliance(
                solution_steps=solution_plan.solution_steps,
                relevant_policies=relevant_policies
            )
            
            # 7. 构建完整结果
            complete_result = {
                "problem": {
                    "description": problem.description,
                    "location": problem.location,
                    "problem_type": problem.problem_type.value,
                    "urgency_level": problem.urgency_level,
                    "stakeholders": problem.stakeholders,
                    "constraints": problem.constraints
                },
                "solution_plan": {
                    "steps": solution_plan.solution_steps,
                    "timeline": solution_plan.timeline,
                    "resource_requirements": solution_plan.resource_requirements,
                    "success_metrics": solution_plan.success_metrics,
                    "local_adaptations": solution_plan.local_adaptations,
                    "risk_assessment": solution_plan.risk_assessment
                },
                "case_references": [
                    {
                        "title": case.title,
                        "problem_type": case.problem_type,
                        "similarity_score": case.similarity_score,
                        "key_measures": case.key_measures,
                        "success_factors": case.success_factors
                    }
                    for case in similar_cases
                ],
                "policy_references": [
                    {
                        "title": policy.title,
                        "admin_level": policy.admin_level,
                        "relevance_score": policy.relevance_score,
                        "key_provisions": policy.key_provisions,
                        "compliance_requirements": policy.compliance_requirements
                    }
                    for policy in relevant_policies
                ],
                "evaluation": evaluation_result,
                "compliance_check": compliance_check,
                "generation_metadata": {
                    "generated_at": solution_plan.generated_at.isoformat(),
                    "system_version": "1.0",
                    "processing_time": "计算中..."
                }
            }
            
            logger.info("治理问题处理完成")
            return complete_result
            
        except Exception as e:
            logger.error(f"处理治理问题失败: {e}")
            return {
                "error": str(e),
                "problem_description": problem_description,
                "location": location,
                "timestamp": datetime.now().isoformat()
            }
    
    def _infer_problem_type(self, problem_description: str) -> ProblemType:
        """推断问题类型"""
        description_lower = problem_description.lower()
        
        type_keywords = {
            ProblemType.NEIGHBOR_DISPUTE: ['邻里', '纠纷', '矛盾', '争吵', '冲突', '邻居'],
            ProblemType.ENVIRONMENT_GOVERNANCE: ['垃圾', '环境', '卫生', '绿化', '污染', '分类'],
            ProblemType.COMMUNITY_SERVICE: ['服务', '便民', '社区', '居民', '公共'],
            ProblemType.SAFETY_MANAGEMENT: ['安全', '消防', '治安', '防范', '监控'],
            ProblemType.POLICY_PROMOTION: ['宣传', '政策', '解读', '培训', '教育'],
            ProblemType.ELDERLY_SERVICE: ['养老', '老年', '老人', '敬老'],
            ProblemType.PARKING_MANAGEMENT: ['停车', '车位', '交通'],
            ProblemType.DIGITAL_DIVIDE: ['智能', '手机', '数字', '网络', '健康码']
        }
        
        for problem_type, keywords in type_keywords.items():
            if any(keyword in description_lower for keyword in keywords):
                return problem_type
        
        return ProblemType.OTHER
    
    def get_system_status(self) -> Dict[str, Any]:
        """获取系统状态"""
        try:
            status = {
                "system_initialized": self.is_initialized,
                "subsystems": {},
                "statistics": {}
            }
            
            if self.is_initialized:
                # 获取各子系统状态
                status["subsystems"]["case_engine"] = self.case_engine.get_case_statistics()
                status["subsystems"]["policy_engine"] = self.policy_engine.get_policy_statistics()
                status["subsystems"]["evaluation_engine"] = self.evaluation_engine.get_evaluation_statistics()
                
                # 系统统计
                status["statistics"]["total_cases"] = status["subsystems"]["case_engine"].get("total_cases", 0)
                status["statistics"]["total_evaluations"] = status["subsystems"]["evaluation_engine"].get("total_evaluations", 0)
            
            return status
            
        except Exception as e:
            logger.error(f"获取系统状态失败: {e}")
            return {"error": str(e)}
    
    def batch_solve_problems(
        self, 
        problems: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """批量处理多个问题"""
        results = []
        
        for i, problem_data in enumerate(problems):
            try:
                logger.info(f"处理第 {i+1}/{len(problems)} 个问题...")
                
                result = self.solve_governance_problem(
                    problem_description=problem_data.get("description", ""),
                    location=problem_data.get("location", ""),
                    urgency_level=problem_data.get("urgency_level", 3),
                    stakeholders=problem_data.get("stakeholders", []),
                    constraints=problem_data.get("constraints", []),
                    expected_outcome=problem_data.get("expected_outcome", ""),
                    timeline=problem_data.get("timeline"),
                    budget_range=problem_data.get("budget_range")
                )
                
                result["batch_index"] = i
                results.append(result)
                
            except Exception as e:
                logger.error(f"批量处理第 {i+1} 个问题失败: {e}")
                results.append({
                    "batch_index": i,
                    "error": str(e),
                    "problem_data": problem_data
                })
        
        return results
    
    def compare_solutions(
        self, 
        problem_description: str,
        location: str,
        alternative_approaches: List[str] = None
    ) -> Dict[str, Any]:
        """比较不同解决方案"""
        try:
            # 生成主要解决方案
            main_solution = self.solve_governance_problem(
                problem_description=problem_description,
                location=location
            )
            
            solutions = [main_solution]
            
            # 如果有替代方案，也生成解决方案
            if alternative_approaches:
                for approach in alternative_approaches:
                    modified_description = f"{problem_description} (采用{approach}方式)"
                    alt_solution = self.solve_governance_problem(
                        problem_description=modified_description,
                        location=location
                    )
                    alt_solution["approach"] = approach
                    solutions.append(alt_solution)
            
            # 比较评估结果
            comparison_result = {
                "problem_description": problem_description,
                "location": location,
                "solutions": solutions,
                "comparison_summary": {
                    "best_solution_index": 0,
                    "best_score": 0.0,
                    "score_differences": []
                }
            }
            
            # 找出最佳方案
            best_score = 0.0
            best_index = 0
            
            for i, solution in enumerate(solutions):
                if "evaluation" in solution:
                    score = solution["evaluation"].get("overall_score", 0.0)
                    if score > best_score:
                        best_score = score
                        best_index = i
            
            comparison_result["comparison_summary"]["best_solution_index"] = best_index
            comparison_result["comparison_summary"]["best_score"] = best_score
            
            return comparison_result
            
        except Exception as e:
            logger.error(f"比较解决方案失败: {e}")
            return {"error": str(e)}