"""
评估引擎 - 方案评估和反馈模块
负责解决方案的质量评估、可行性分析和持续改进
"""
import json
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
from dataclasses import asdict
from enum import Enum

from utils.logger import logger
from src.governance_agent import SolutionPlan, GovernanceProblem

class EvaluationCriteria(Enum):
    """评估标准枚举"""
    FEASIBILITY = "可行性"
    EFFECTIVENESS = "有效性"
    COMPLIANCE = "合规性"
    SUSTAINABILITY = "可持续性"
    COST_EFFICIENCY = "成本效益"
    STAKEHOLDER_ACCEPTANCE = "利益相关方接受度"

class EvaluationLevel(Enum):
    """评估等级枚举"""
    EXCELLENT = "优秀"
    GOOD = "良好"
    FAIR = "一般"
    POOR = "较差"
    UNACCEPTABLE = "不可接受"

class EvaluationEngine:
    """评估引擎"""
    
    def __init__(self):
        """初始化评估引擎"""
        logger.info("初始化评估引擎...")
        
        # 评估权重配置
        self.evaluation_weights = {
            EvaluationCriteria.FEASIBILITY.value: 0.25,
            EvaluationCriteria.EFFECTIVENESS.value: 0.20,
            EvaluationCriteria.COMPLIANCE.value: 0.20,
            EvaluationCriteria.SUSTAINABILITY.value: 0.15,
            EvaluationCriteria.COST_EFFICIENCY.value: 0.10,
            EvaluationCriteria.STAKEHOLDER_ACCEPTANCE.value: 0.10
        }
        
        # 评估历史记录
        self.evaluation_history = []
        
        logger.info("评估引擎初始化完成")
    
    def evaluate_solution(self, solution_plan: SolutionPlan) -> Dict[str, Any]:
        """
        全面评估解决方案
        
        Args:
            solution_plan: 解决方案计划
            
        Returns:
            评估结果
        """
        try:
            logger.info("开始评估解决方案...")
            
            # 各维度评估
            feasibility_score = self._evaluate_feasibility(solution_plan)
            effectiveness_score = self._evaluate_effectiveness(solution_plan)
            compliance_score = self._evaluate_compliance(solution_plan)
            sustainability_score = self._evaluate_sustainability(solution_plan)
            cost_efficiency_score = self._evaluate_cost_efficiency(solution_plan)
            stakeholder_score = self._evaluate_stakeholder_acceptance(solution_plan)
            
            # 计算综合得分
            overall_score = (
                feasibility_score * self.evaluation_weights[EvaluationCriteria.FEASIBILITY.value] +
                effectiveness_score * self.evaluation_weights[EvaluationCriteria.EFFECTIVENESS.value] +
                compliance_score * self.evaluation_weights[EvaluationCriteria.COMPLIANCE.value] +
                sustainability_score * self.evaluation_weights[EvaluationCriteria.SUSTAINABILITY.value] +
                cost_efficiency_score * self.evaluation_weights[EvaluationCriteria.COST_EFFICIENCY.value] +
                stakeholder_score * self.evaluation_weights[EvaluationCriteria.STAKEHOLDER_ACCEPTANCE.value]
            )
            
            # 确定评估等级
            evaluation_level = self._determine_evaluation_level(overall_score)
            
            # 生成改进建议
            improvement_suggestions = self._generate_improvement_suggestions(
                solution_plan, {
                    EvaluationCriteria.FEASIBILITY.value: feasibility_score,
                    EvaluationCriteria.EFFECTIVENESS.value: effectiveness_score,
                    EvaluationCriteria.COMPLIANCE.value: compliance_score,
                    EvaluationCriteria.SUSTAINABILITY.value: sustainability_score,
                    EvaluationCriteria.COST_EFFICIENCY.value: cost_efficiency_score,
                    EvaluationCriteria.STAKEHOLDER_ACCEPTANCE.value: stakeholder_score
                }
            )
            
            # 构建评估结果
            evaluation_result = {
                "overall_score": round(overall_score, 2),
                "evaluation_level": evaluation_level.value,
                "detailed_scores": {
                    EvaluationCriteria.FEASIBILITY.value: round(feasibility_score, 2),
                    EvaluationCriteria.EFFECTIVENESS.value: round(effectiveness_score, 2),
                    EvaluationCriteria.COMPLIANCE.value: round(compliance_score, 2),
                    EvaluationCriteria.SUSTAINABILITY.value: round(sustainability_score, 2),
                    EvaluationCriteria.COST_EFFICIENCY.value: round(cost_efficiency_score, 2),
                    EvaluationCriteria.STAKEHOLDER_ACCEPTANCE.value: round(stakeholder_score, 2)
                },
                "strengths": self._identify_strengths(solution_plan),
                "weaknesses": self._identify_weaknesses(solution_plan),
                "improvement_suggestions": improvement_suggestions,
                "risk_assessment": self._assess_implementation_risks(solution_plan),
                "success_probability": self._estimate_success_probability(overall_score),
                "evaluation_time": datetime.now().isoformat(),
                "evaluator": "AI评估引擎"
            }
            
            # 记录评估历史
            self.evaluation_history.append({
                "problem_description": solution_plan.problem.description,
                "evaluation_result": evaluation_result,
                "timestamp": datetime.now()
            })
            
            logger.info(f"解决方案评估完成，综合得分: {overall_score:.2f}")
            return evaluation_result
            
        except Exception as e:
            logger.error(f"评估解决方案失败: {e}")
            return {
                "overall_score": 0.0,
                "evaluation_level": EvaluationLevel.UNACCEPTABLE.value,
                "error": str(e),
                "evaluation_time": datetime.now().isoformat()
            }
    
    def _evaluate_feasibility(self, solution_plan: SolutionPlan) -> float:
        """评估可行性"""
        score = 0.0
        
        # 检查步骤的具体性和可操作性
        if solution_plan.solution_steps:
            concrete_steps = sum(1 for step in solution_plan.solution_steps 
                               if len(step.get('description', '')) > 20)
            score += (concrete_steps / len(solution_plan.solution_steps)) * 30
        
        # 检查资源需求的合理性
        if solution_plan.resource_requirements:
            if solution_plan.resource_requirements.get('human_resources'):
                score += 20
            if solution_plan.resource_requirements.get('financial_resources'):
                score += 15
        
        # 检查时间安排的合理性
        if solution_plan.timeline:
            if solution_plan.timeline.get('overall_duration'):
                score += 15
        
        # 检查风险评估的完整性
        if solution_plan.risk_assessment:
            if solution_plan.risk_assessment.get('key_risks'):
                score += 20
        
        return min(score, 100.0)
    
    def _evaluate_effectiveness(self, solution_plan: SolutionPlan) -> float:
        """评估有效性"""
        score = 0.0
        
        # 检查是否有明确的成功指标
        if solution_plan.success_metrics:
            score += len(solution_plan.success_metrics) * 10
        
        # 检查案例参考的相关性
        if solution_plan.case_references:
            high_similarity_cases = sum(1 for case in solution_plan.case_references 
                                      if case.similarity_score > 0.7)
            score += high_similarity_cases * 15
        
        # 检查解决方案的系统性
        if len(solution_plan.solution_steps) >= 5:
            score += 20
        
        # 检查本地化适配
        if solution_plan.local_adaptations:
            score += len(solution_plan.local_adaptations) * 5
        
        return min(score, 100.0)
    
    def _evaluate_compliance(self, solution_plan: SolutionPlan) -> float:
        """评估合规性"""
        score = 0.0
        
        # 检查政策参考的完整性
        if solution_plan.policy_references:
            score += len(solution_plan.policy_references) * 20
            
            # 检查政策层级的多样性
            levels = set(policy.admin_level for policy in solution_plan.policy_references)
            score += len(levels) * 10
        
        # 检查风险评估中的合规风险
        if solution_plan.risk_assessment:
            risk_content = solution_plan.risk_assessment.get('assessment_content', '')
            if '合规' in risk_content or '政策' in risk_content:
                score += 20
        
        return min(score, 100.0)
    
    def _evaluate_sustainability(self, solution_plan: SolutionPlan) -> float:
        """评估可持续性"""
        score = 0.0
        
        # 检查长期规划
        long_term_metrics = [metric for metric in solution_plan.success_metrics 
                           if '长期' in metric or '持续' in metric]
        score += len(long_term_metrics) * 15
        
        # 检查制度建设
        institutional_steps = [step for step in solution_plan.solution_steps 
                             if '制度' in step.get('description', '') or 
                                '机制' in step.get('description', '')]
        score += len(institutional_steps) * 20
        
        # 检查资源的可持续性
        if solution_plan.resource_requirements:
            if '持续' in str(solution_plan.resource_requirements):
                score += 25
        
        return min(score, 100.0)
    
    def _evaluate_cost_efficiency(self, solution_plan: SolutionPlan) -> float:
        """评估成本效益"""
        score = 50.0  # 基础分
        
        # 检查资源需求的详细程度
        if solution_plan.resource_requirements:
            if solution_plan.resource_requirements.get('financial_resources'):
                score += 20
            if solution_plan.resource_requirements.get('human_resources'):
                score += 15
        
        # 检查成本控制措施
        cost_control_steps = [step for step in solution_plan.solution_steps 
                            if '成本' in step.get('description', '') or 
                               '预算' in step.get('description', '')]
        score += len(cost_control_steps) * 15
        
        return min(score, 100.0)
    
    def _evaluate_stakeholder_acceptance(self, solution_plan: SolutionPlan) -> float:
        """评估利益相关方接受度"""
        score = 0.0
        
        # 检查利益相关方的参与程度
        stakeholder_count = len(solution_plan.problem.stakeholders)
        score += min(stakeholder_count * 15, 60)
        
        # 检查沟通协调步骤
        communication_steps = [step for step in solution_plan.solution_steps 
                             if '沟通' in step.get('description', '') or 
                                '协调' in step.get('description', '') or
                                '征求' in step.get('description', '')]
        score += len(communication_steps) * 20
        
        return min(score, 100.0)
    
    def _determine_evaluation_level(self, overall_score: float) -> EvaluationLevel:
        """确定评估等级"""
        if overall_score >= 90:
            return EvaluationLevel.EXCELLENT
        elif overall_score >= 80:
            return EvaluationLevel.GOOD
        elif overall_score >= 70:
            return EvaluationLevel.FAIR
        elif overall_score >= 60:
            return EvaluationLevel.POOR
        else:
            return EvaluationLevel.UNACCEPTABLE
    
    def _generate_improvement_suggestions(
        self, 
        solution_plan: SolutionPlan, 
        detailed_scores: Dict[str, float]
    ) -> List[str]:
        """生成改进建议"""
        suggestions = []
        
        # 基于各维度得分生成建议
        for criterion, score in detailed_scores.items():
            if score < 70:
                if criterion == EvaluationCriteria.FEASIBILITY.value:
                    suggestions.append("建议进一步细化实施步骤，增强方案的可操作性")
                elif criterion == EvaluationCriteria.EFFECTIVENESS.value:
                    suggestions.append("建议增加更多相关成功案例参考，提高方案有效性")
                elif criterion == EvaluationCriteria.COMPLIANCE.value:
                    suggestions.append("建议补充更多政策法规依据，确保方案合规性")
                elif criterion == EvaluationCriteria.SUSTAINABILITY.value:
                    suggestions.append("建议加强长效机制建设，提高方案可持续性")
                elif criterion == EvaluationCriteria.COST_EFFICIENCY.value:
                    suggestions.append("建议优化资源配置，提高成本效益")
                elif criterion == EvaluationCriteria.STAKEHOLDER_ACCEPTANCE.value:
                    suggestions.append("建议加强利益相关方沟通，提高方案接受度")
        
        # 基于整体情况的建议
        if len(solution_plan.solution_steps) < 5:
            suggestions.append("建议增加更多实施步骤，使方案更加完整")
        
        if not solution_plan.success_metrics:
            suggestions.append("建议设定明确的成功评估指标")
        
        if not solution_plan.local_adaptations:
            suggestions.append("建议增加本地化适配建议")
        
        return suggestions[:5]  # 最多5个建议
    
    def _identify_strengths(self, solution_plan: SolutionPlan) -> List[str]:
        """识别方案优势"""
        strengths = []
        
        if len(solution_plan.case_references) >= 3:
            strengths.append("参考了多个相关成功案例")
        
        if len(solution_plan.policy_references) >= 2:
            strengths.append("有充分的政策法规支撑")
        
        if len(solution_plan.solution_steps) >= 7:
            strengths.append("实施步骤详细完整")
        
        if solution_plan.risk_assessment.get('key_risks'):
            strengths.append("进行了全面的风险评估")
        
        if solution_plan.local_adaptations:
            strengths.append("考虑了本地化适配")
        
        return strengths
    
    def _identify_weaknesses(self, solution_plan: SolutionPlan) -> List[str]:
        """识别方案弱点"""
        weaknesses = []
        
        if not solution_plan.case_references:
            weaknesses.append("缺少成功案例参考")
        
        if not solution_plan.policy_references:
            weaknesses.append("缺少政策法规依据")
        
        if len(solution_plan.solution_steps) < 5:
            weaknesses.append("实施步骤不够详细")
        
        if not solution_plan.success_metrics:
            weaknesses.append("缺少明确的成功指标")
        
        if not solution_plan.resource_requirements.get('financial_resources'):
            weaknesses.append("缺少资金需求评估")
        
        return weaknesses
    
    def _assess_implementation_risks(self, solution_plan: SolutionPlan) -> Dict[str, Any]:
        """评估实施风险"""
        risks = {
            "high_risks": [],
            "medium_risks": [],
            "low_risks": [],
            "overall_risk_level": "中等"
        }
        
        # 基于问题紧急程度评估风险
        urgency = solution_plan.problem.urgency_level
        if urgency >= 4:
            risks["high_risks"].append("问题紧急程度高，实施压力大")
        elif urgency >= 3:
            risks["medium_risks"].append("问题具有一定紧急性")
        else:
            risks["low_risks"].append("问题紧急程度较低")
        
        # 基于利益相关方数量评估风险
        stakeholder_count = len(solution_plan.problem.stakeholders)
        if stakeholder_count >= 5:
            risks["medium_risks"].append("涉及利益相关方较多，协调难度大")
        elif stakeholder_count <= 2:
            risks["low_risks"].append("涉及利益相关方较少，协调相对容易")
        
        # 基于约束条件评估风险
        constraints = solution_plan.problem.constraints
        if '预算' in str(constraints) or '资金' in str(constraints):
            risks["high_risks"].append("存在预算约束风险")
        if '人手' in str(constraints) or '人力' in str(constraints):
            risks["medium_risks"].append("存在人力资源不足风险")
        
        # 确定整体风险等级
        if len(risks["high_risks"]) >= 2:
            risks["overall_risk_level"] = "高"
        elif len(risks["high_risks"]) >= 1 or len(risks["medium_risks"]) >= 3:
            risks["overall_risk_level"] = "中等"
        else:
            risks["overall_risk_level"] = "低"
        
        return risks
    
    def _estimate_success_probability(self, overall_score: float) -> str:
        """估算成功概率"""
        if overall_score >= 90:
            return "90%以上"
        elif overall_score >= 80:
            return "80-90%"
        elif overall_score >= 70:
            return "70-80%"
        elif overall_score >= 60:
            return "60-70%"
        else:
            return "60%以下"
    
    def get_evaluation_statistics(self) -> Dict[str, Any]:
        """获取评估统计信息"""
        if not self.evaluation_history:
            return {"total_evaluations": 0}
        
        total_evaluations = len(self.evaluation_history)
        
        # 计算平均分数
        total_score = sum(eval_record["evaluation_result"]["overall_score"] 
                         for eval_record in self.evaluation_history)
        average_score = total_score / total_evaluations
        
        # 统计评估等级分布
        level_distribution = {}
        for eval_record in self.evaluation_history:
            level = eval_record["evaluation_result"]["evaluation_level"]
            level_distribution[level] = level_distribution.get(level, 0) + 1
        
        return {
            "total_evaluations": total_evaluations,
            "average_score": round(average_score, 2),
            "level_distribution": level_distribution,
            "latest_evaluation": self.evaluation_history[-1]["timestamp"].isoformat()
        }
    
    def compare_solutions(
        self, 
        solution_plans: List[SolutionPlan]
    ) -> Dict[str, Any]:
        """比较多个解决方案"""
        if len(solution_plans) < 2:
            return {"error": "需要至少两个方案进行比较"}
        
        evaluations = []
        for i, plan in enumerate(solution_plans):
            evaluation = self.evaluate_solution(plan)
            evaluation["solution_index"] = i
            evaluations.append(evaluation)
        
        # 排序
        evaluations.sort(key=lambda x: x["overall_score"], reverse=True)
        
        return {
            "best_solution": evaluations[0],
            "all_evaluations": evaluations,
            "comparison_summary": {
                "best_score": evaluations[0]["overall_score"],
                "worst_score": evaluations[-1]["overall_score"],
                "score_range": evaluations[0]["overall_score"] - evaluations[-1]["overall_score"]
            }
        }

if __name__ == "__main__":
    # 测试评估引擎
    try:
        from src.governance_agent import (
            GovernanceProblem, ProblemType, CaseReference, PolicyReference, SolutionPlan
        )
        
        engine = EvaluationEngine()
        
        # 创建测试解决方案计划
        test_problem = GovernanceProblem(
            description="测试问题",
            location="测试地区",
            problem_type=ProblemType.ENVIRONMENT_GOVERNANCE,
            urgency_level=3,
            stakeholders=["居民", "物业", "社区"],
            constraints=["预算有限"],
            expected_outcome="解决问题"
        )
        
        test_solution_plan = SolutionPlan(
            problem=test_problem,
            case_references=[],
            policy_references=[],
            solution_steps=[
                {"step": 1, "description": "第一步测试", "duration": "1周"},
                {"step": 2, "description": "第二步测试", "duration": "2周"}
            ],
            risk_assessment={"key_risks": ["测试风险"]},
            resource_requirements={"human_resources": ["测试人员"]},
            success_metrics=["测试指标"],
            timeline={"overall_duration": "3周"},
            local_adaptations=["测试适配"],
            generated_at=datetime.now()
        )
        
        # 评估解决方案
        evaluation_result = engine.evaluate_solution(test_solution_plan)
        
        print("✅ 评估引擎测试成功")
        print(f"   综合得分: {evaluation_result['overall_score']}")
        print(f"   评估等级: {evaluation_result['evaluation_level']}")
        print(f"   改进建议数: {len(evaluation_result['improvement_suggestions'])}")
        
        # 获取统计信息
        stats = engine.get_evaluation_statistics()
        print(f"   评估历史: {stats['total_evaluations']} 次")
        
    except Exception as e:
        print(f"测试失败: {e}")
        import traceback
        traceback.print_exc()