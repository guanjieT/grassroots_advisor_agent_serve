"""
解决方案生成器 - 核心方案生成模块
基于案例和政策生成定制化的治理解决方案
"""
import json
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from langchain_community.llms import Tongyi
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser

from config import config
from utils.logger import logger
from src.governance_agent import (
    GovernanceProblem, CaseReference, PolicyReference, 
    SolutionPlan, ProblemType, AdminLevel
)

class SolutionGenerator:
    """解决方案生成器"""
    
    def __init__(self):
        """初始化解决方案生成器"""
        logger.info("初始化解决方案生成器...")
        
        # 初始化LLM
        self.llm = Tongyi(
            dashscope_api_key=config.DASHSCOPE_API_KEY,
            model_name=config.LLM_MODEL,
            temperature=0.2,  # 较低温度确保方案的一致性
            max_tokens=3000
        )
        
        # 设置提示模板
        self._setup_prompts()
        
        # 方案模板库
        self.solution_templates = self._load_solution_templates()
        
        logger.info("解决方案生成器初始化完成")
    
    def _setup_prompts(self):
        """设置提示模板"""
        
        # 主要解决方案生成提示
        self.main_solution_prompt = PromptTemplate(
            input_variables=[
                "problem", "location", "urgency", "stakeholders", 
                "case_references", "policy_references", "constraints"
            ],
            template="""你是一个专业的基层治理专家，请基于成功案例和政策法规，为特定问题生成详细的解决方案。

## 问题信息
**地区**: {location}
**问题描述**: {problem}
**紧急程度**: {urgency}/5
**涉及方**: {stakeholders}
**约束条件**: {constraints}

## 参考成功案例
{case_references}

## 相关政策法规
{policy_references}

## 请生成结构化的解决方案，包含以下内容：

### 1. 问题深度分析
- 根本原因分析（至少3个层面）
- 利益相关方分析
- 风险因素识别

### 2. 解决方案设计
**总体策略**: 基于成功案例的核心经验，提出总体解决思路

**具体步骤**: 请按以下JSON格式提供7-10个具体步骤：
```json
[
  {{
    "step": 1,
    "title": "步骤标题",
    "description": "详细描述",
    "duration": "预期时间",
    "responsible_party": "责任方",
    "resources_needed": ["所需资源1", "所需资源2"],
    "success_criteria": "成功标准",
    "risk_mitigation": "风险缓解措施"
  }}
]
```

### 3. 政策合规保障
- 法律法规依据
- 合规性要求
- 审批流程

### 4. 地区适配建议
- 本地化调整要点
- 文化适应性考虑
- 特殊情况处理

### 5. 资源需求评估
- 人力资源需求
- 财政资源需求
- 技术资源需求
- 时间资源需求

### 6. 风险评估与应对
- 主要风险点（至少5个）
- 风险等级评估
- 应对预案

### 7. 成效评估体系
- 短期指标（1-3个月）
- 中期指标（3-6个月）
- 长期指标（6个月以上）
- 评估方法和频次

请确保方案具体可操作，符合政策要求，并充分借鉴成功案例经验。

解决方案："""
        )
        
        # 风险评估提示
        self.risk_assessment_prompt = PromptTemplate(
            input_variables=["problem", "solution_steps", "location"],
            template="""请对以下基层治理解决方案进行风险评估：

**问题**: {problem}
**地区**: {location}
**解决方案步骤**: {solution_steps}

请从以下维度进行风险评估：
1. 政策风险 - 是否符合现行政策法规
2. 实施风险 - 执行过程中可能遇到的困难
3. 资源风险 - 资源不足或配置不当的风险
4. 社会风险 - 可能引发的社会反应或冲突
5. 时间风险 - 时间安排不当的风险

对每个风险提供：
- 风险等级（高/中/低）
- 发生概率（高/中/低）
- 影响程度（高/中/低）
- 应对措施

风险评估结果："""
        )
        
        # 资源需求评估提示
        self.resource_assessment_prompt = PromptTemplate(
            input_variables=["solution_steps", "location", "timeline"],
            template="""请对以下解决方案的资源需求进行详细评估：

**解决方案步骤**: {solution_steps}
**实施地区**: {location}
**时间安排**: {timeline}

请评估以下资源需求：

1. **人力资源**
   - 专职人员需求
   - 兼职人员需求
   - 志愿者需求
   - 专业技能要求

2. **财政资源**
   - 一次性投入
   - 持续运营成本
   - 应急资金储备

3. **技术资源**
   - 设备设施需求
   - 信息系统需求
   - 技术支持需求

4. **其他资源**
   - 场地需求
   - 合作伙伴
   - 外部支持

资源需求评估："""
        )
    
    def _load_solution_templates(self) -> Dict[str, Any]:
        """加载解决方案模板"""
        templates = {
            ProblemType.NEIGHBOR_DISPUTE.value: {
                "key_steps": ["调研了解", "沟通协调", "制定方案", "组织实施", "跟踪评估"],
                "typical_duration": "2-4周",
                "main_stakeholders": ["居民", "社区", "物业", "调解员"],
                "success_factors": ["及时介入", "公正调解", "建立机制"]
            },
            ProblemType.ENVIRONMENT_GOVERNANCE.value: {
                "key_steps": ["问题调研", "制度建设", "宣传教育", "设施完善", "监督管理"],
                "typical_duration": "1-3个月",
                "main_stakeholders": ["居民", "物业", "环保部门", "志愿者"],
                "success_factors": ["制度保障", "全民参与", "长效管理"]
            },
            ProblemType.COMMUNITY_SERVICE.value: {
                "key_steps": ["需求调研", "资源整合", "服务设计", "试点实施", "推广优化"],
                "typical_duration": "1-6个月",
                "main_stakeholders": ["居民", "社区", "服务机构", "政府部门"],
                "success_factors": ["需求导向", "资源整合", "持续改进"]
            }
        }
        
        return templates
    
    def generate_solution(
        self,
        problem: GovernanceProblem,
        case_references: List[CaseReference],
        policy_references: List[PolicyReference]
    ) -> SolutionPlan:
        """
        生成完整的解决方案
        
        Args:
            problem: 治理问题
            case_references: 参考案例
            policy_references: 参考政策
            
        Returns:
            完整的解决方案计划
        """
        try:
            logger.info(f"生成解决方案: {problem.description[:50]}...")
            
            # 1. 生成主要解决方案内容
            solution_content = self._generate_main_solution(
                problem, case_references, policy_references
            )
            
            # 2. 解析解决方案步骤
            solution_steps = self._parse_solution_steps(solution_content)
            
            # 3. 生成风险评估
            risk_assessment = self._generate_risk_assessment(
                problem, solution_steps
            )
            
            # 4. 生成资源需求评估
            resource_requirements = self._generate_resource_assessment(
                solution_steps, problem.location
            )
            
            # 5. 生成时间安排
            timeline = self._generate_timeline(solution_steps, problem.timeline)
            
            # 6. 提取成功指标
            success_metrics = self._extract_success_metrics(solution_content)
            
            # 7. 生成本地化建议
            local_adaptations = self._generate_local_adaptations(
                problem, case_references
            )
            
            # 构建完整的解决方案计划
            solution_plan = SolutionPlan(
                problem=problem,
                case_references=case_references,
                policy_references=policy_references,
                solution_steps=solution_steps,
                risk_assessment=risk_assessment,
                resource_requirements=resource_requirements,
                success_metrics=success_metrics,
                timeline=timeline,
                local_adaptations=local_adaptations,
                generated_at=datetime.now()
            )
            
            logger.info("解决方案生成完成")
            return solution_plan
            
        except Exception as e:
            logger.error(f"生成解决方案失败: {e}")
            raise
    
    def _generate_main_solution(
        self,
        problem: GovernanceProblem,
        case_references: List[CaseReference],
        policy_references: List[PolicyReference]
    ) -> str:
        """生成主要解决方案内容"""
        
        # 格式化案例参考
        case_text = self._format_case_references(case_references)
        
        # 格式化政策参考
        policy_text = self._format_policy_references(policy_references)
        
        # 生成解决方案
        prompt_input = {
            "problem": problem.description,
            "location": problem.location,
            "urgency": problem.urgency_level,
            "stakeholders": ", ".join(problem.stakeholders),
            "constraints": ", ".join(problem.constraints),
            "case_references": case_text,
            "policy_references": policy_text
        }
        
        solution = self.main_solution_prompt.format(**prompt_input)
        result = self.llm.invoke(solution)
        
        return result
    
    def _format_case_references(self, case_references: List[CaseReference]) -> str:
        """格式化案例参考"""
        if not case_references:
            return "暂无相关成功案例"
        
        formatted_cases = []
        for i, case in enumerate(case_references, 1):
            case_text = f"""
### 案例 {i}: {case.title}
**问题类型**: {case.problem_type}
**相似度**: {case.similarity_score:.2f}
**关键措施**: {'; '.join(case.key_measures[:3])}
**成功因素**: {'; '.join(case.success_factors[:2])}
**适用条件**: {'; '.join(case.applicable_conditions[:2])}
"""
            formatted_cases.append(case_text)
        
        return '\n'.join(formatted_cases)
    
    def _format_policy_references(self, policy_references: List[PolicyReference]) -> str:
        """格式化政策参考"""
        if not policy_references:
            return "请参考当地相关政策法规"
        
        formatted_policies = []
        for i, policy in enumerate(policy_references, 1):
            policy_text = f"""
### 政策 {i}: {policy.title}
**层级**: {policy.admin_level}
**相关性**: {policy.relevance_score:.2f}
**关键条款**: {'; '.join(policy.key_provisions[:2])}
**合规要求**: {'; '.join(policy.compliance_requirements[:2])}
"""
            formatted_policies.append(policy_text)
        
        return '\n'.join(formatted_policies)
    
    def _parse_solution_steps(self, solution_content: str) -> List[Dict[str, Any]]:
        """解析解决方案步骤"""
        try:
            # 尝试从内容中提取JSON格式的步骤
            import re
            
            json_pattern = r'```json\s*(\[.*?\])\s*```'
            json_match = re.search(json_pattern, solution_content, re.DOTALL)
            
            if json_match:
                json_str = json_match.group(1)
                steps = json.loads(json_str)
                return steps
            
            # 如果没有找到JSON格式，尝试解析文本格式
            return self._parse_text_steps(solution_content)
            
        except Exception as e:
            logger.warning(f"解析解决方案步骤失败: {e}")
            return self._generate_default_steps()
    
    def _parse_text_steps(self, content: str) -> List[Dict[str, Any]]:
        """解析文本格式的步骤"""
        steps = []
        lines = content.split('\n')
        
        current_step = None
        step_counter = 1
        
        for line in lines:
            line = line.strip()
            
            # 检测步骤标题
            if (line.startswith(f'{step_counter}.') or 
                line.startswith(f'第{step_counter}') or
                '步骤' in line):
                
                if current_step:
                    steps.append(current_step)
                
                current_step = {
                    "step": step_counter,
                    "title": line,
                    "description": "",
                    "duration": "待定",
                    "responsible_party": "相关部门",
                    "resources_needed": [],
                    "success_criteria": "按计划完成",
                    "risk_mitigation": "加强监督"
                }
                step_counter += 1
            
            elif current_step and line:
                current_step["description"] += line + " "
        
        if current_step:
            steps.append(current_step)
        
        return steps[:10]  # 最多10个步骤
    
    def _generate_default_steps(self) -> List[Dict[str, Any]]:
        """生成默认步骤"""
        return [
            {
                "step": 1,
                "title": "问题调研分析",
                "description": "深入了解问题现状，分析根本原因",
                "duration": "1周",
                "responsible_party": "社区工作组",
                "resources_needed": ["调研人员", "调研工具"],
                "success_criteria": "完成问题分析报告",
                "risk_mitigation": "多方验证信息准确性"
            },
            {
                "step": 2,
                "title": "制定解决方案",
                "description": "基于调研结果制定具体解决方案",
                "duration": "3-5天",
                "responsible_party": "工作小组",
                "resources_needed": ["专业人员", "参考资料"],
                "success_criteria": "方案获得各方认可",
                "risk_mitigation": "充分征求意见"
            }
        ]
    
    def _generate_risk_assessment(
        self, 
        problem: GovernanceProblem, 
        solution_steps: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """生成风险评估"""
        try:
            steps_text = json.dumps(solution_steps, ensure_ascii=False, indent=2)
            
            risk_prompt = self.risk_assessment_prompt.format(
                problem=problem.description,
                solution_steps=steps_text,
                location=problem.location
            )
            
            risk_result = self.llm.invoke(risk_prompt)
            
            # 解析风险评估结果
            return {
                "assessment_content": risk_result,
                "overall_risk_level": "中等",
                "key_risks": self._extract_key_risks(risk_result),
                "mitigation_strategies": self._extract_mitigation_strategies(risk_result)
            }
            
        except Exception as e:
            logger.error(f"生成风险评估失败: {e}")
            return {
                "assessment_content": "风险评估生成失败",
                "overall_risk_level": "未知",
                "key_risks": ["需要人工评估风险"],
                "mitigation_strategies": ["建议专业人士评估"]
            }
    
    def _generate_resource_assessment(
        self, 
        solution_steps: List[Dict[str, Any]], 
        location: str
    ) -> Dict[str, Any]:
        """生成资源需求评估"""
        try:
            steps_text = json.dumps(solution_steps, ensure_ascii=False, indent=2)
            timeline = "根据步骤安排"
            
            resource_prompt = self.resource_assessment_prompt.format(
                solution_steps=steps_text,
                location=location,
                timeline=timeline
            )
            
            resource_result = self.llm.invoke(resource_prompt)
            
            return {
                "assessment_content": resource_result,
                "human_resources": self._extract_human_resources(solution_steps),
                "financial_resources": self._extract_financial_resources(solution_steps),
                "technical_resources": self._extract_technical_resources(solution_steps),
                "other_resources": self._extract_other_resources(solution_steps)
            }
            
        except Exception as e:
            logger.error(f"生成资源评估失败: {e}")
            return {
                "assessment_content": "资源评估生成失败",
                "human_resources": ["需要评估人力需求"],
                "financial_resources": ["需要评估资金需求"],
                "technical_resources": ["需要评估技术需求"],
                "other_resources": ["需要评估其他资源需求"]
            }
    
    def _generate_timeline(
        self, 
        solution_steps: List[Dict[str, Any]], 
        expected_timeline: Optional[str]
    ) -> Dict[str, str]:
        """生成时间安排"""
        timeline = {}
        
        if expected_timeline:
            timeline["overall_duration"] = expected_timeline
        else:
            # 根据步骤估算总时间
            total_weeks = len(solution_steps) * 1.5  # 平均每步1.5周
            timeline["overall_duration"] = f"{int(total_weeks)}周"
        
        # 为每个步骤分配时间
        for i, step in enumerate(solution_steps):
            step_key = f"step_{step.get('step', i+1)}"
            timeline[step_key] = step.get('duration', '1周')
        
        return timeline
    
    def _extract_success_metrics(self, solution_content: str) -> List[str]:
        """提取成功指标"""
        metrics = []
        
        # 查找包含指标关键词的句子
        metric_keywords = ['指标', '标准', '目标', '效果', '成功', '完成率']
        
        sentences = solution_content.split('。')
        for sentence in sentences:
            if any(keyword in sentence for keyword in metric_keywords):
                metrics.append(sentence.strip() + '。')
        
        # 如果没有找到，提供默认指标
        if not metrics:
            metrics = [
                "问题解决率达到80%以上",
                "相关方满意度达到85%以上",
                "方案执行完成率达到90%以上"
            ]
        
        return metrics[:5]  # 最多5个指标
    
    def _generate_local_adaptations(
        self, 
        problem: GovernanceProblem, 
        case_references: List[CaseReference]
    ) -> List[str]:
        """生成本地化建议"""
        adaptations = []
        
        # 基于地区特点的建议
        location = problem.location
        
        if '北京' in location:
            adaptations.append("考虑北京市的政策环境和管理要求")
        elif '上海' in location:
            adaptations.append("结合上海市的国际化特点和管理标准")
        elif '广州' in location or '深圳' in location:
            adaptations.append("考虑珠三角地区的经济发展水平和人口结构")
        
        # 基于问题类型的建议
        if problem.problem_type == ProblemType.NEIGHBOR_DISPUTE:
            adaptations.append("重视邻里关系的文化传统")
        elif problem.problem_type == ProblemType.ENVIRONMENT_GOVERNANCE:
            adaptations.append("结合当地环保要求和居民习惯")
        
        # 基于案例经验的建议
        for case in case_references:
            if case.applicable_conditions:
                adaptations.extend(case.applicable_conditions[:1])
        
        return adaptations[:5]  # 最多5个建议
    
    def _extract_key_risks(self, risk_content: str) -> List[str]:
        """提取关键风险"""
        risks = []
        risk_keywords = ['风险', '困难', '挑战', '问题', '障碍']
        
        sentences = risk_content.split('。')
        for sentence in sentences:
            if any(keyword in sentence for keyword in risk_keywords):
                risks.append(sentence.strip() + '。')
        
        return risks[:5]
    
    def _extract_mitigation_strategies(self, risk_content: str) -> List[str]:
        """提取缓解策略"""
        strategies = []
        strategy_keywords = ['应对', '缓解', '预防', '措施', '建议']
        
        sentences = risk_content.split('。')
        for sentence in sentences:
            if any(keyword in sentence for keyword in strategy_keywords):
                strategies.append(sentence.strip() + '。')
        
        return strategies[:5]
    
    def _extract_human_resources(self, solution_steps: List[Dict[str, Any]]) -> List[str]:
        """提取人力资源需求"""
        resources = set()
        
        for step in solution_steps:
            responsible = step.get('responsible_party', '')
            if responsible:
                resources.add(responsible)
            
            step_resources = step.get('resources_needed', [])
            for resource in step_resources:
                if '人员' in resource or '工作' in resource:
                    resources.add(resource)
        
        return list(resources)[:5]
    
    def _extract_financial_resources(self, solution_steps: List[Dict[str, Any]]) -> List[str]:
        """提取财政资源需求"""
        resources = []
        
        for step in solution_steps:
            step_resources = step.get('resources_needed', [])
            for resource in step_resources:
                if any(keyword in resource for keyword in ['资金', '费用', '预算', '成本']):
                    resources.append(resource)
        
        if not resources:
            resources = ["需要评估具体资金需求"]
        
        return resources[:3]
    
    def _extract_technical_resources(self, solution_steps: List[Dict[str, Any]]) -> List[str]:
        """提取技术资源需求"""
        resources = []
        
        for step in solution_steps:
            step_resources = step.get('resources_needed', [])
            for resource in step_resources:
                if any(keyword in resource for keyword in ['设备', '系统', '技术', '工具']):
                    resources.append(resource)
        
        if not resources:
            resources = ["基础办公设备和工具"]
        
        return resources[:3]
    
    def _extract_other_resources(self, solution_steps: List[Dict[str, Any]]) -> List[str]:
        """提取其他资源需求"""
        resources = []
        
        for step in solution_steps:
            step_resources = step.get('resources_needed', [])
            for resource in step_resources:
                if not any(keyword in resource for keyword in ['人员', '工作', '资金', '费用', '设备', '系统']):
                    resources.append(resource)
        
        if not resources:
            resources = ["场地支持", "合作伙伴", "政策支持"]
        
        return resources[:3]

if __name__ == "__main__":
    # 测试解决方案生成器
    try:
        from src.governance_agent import GovernanceProblem, ProblemType
        
        generator = SolutionGenerator()
        
        # 创建测试问题
        test_problem = GovernanceProblem(
            description="小区垃圾分类执行不到位，居民积极性不高",
            location="广州市天河区某小区",
            problem_type=ProblemType.ENVIRONMENT_GOVERNANCE,
            urgency_level=3,
            stakeholders=["居民", "物业", "社区", "环保部门"],
            constraints=["预算有限", "人手不足"],
            expected_outcome="提高垃圾分类准确率到85%以上"
        )
        
        # 创建测试案例参考（简化）
        test_cases = [
            CaseReference(
                case_id="test_case_1",
                title="环境卫生整治长效管理",
                problem_type="环境治理",
                similarity_score=0.85,
                key_measures=["制度建设", "宣传教育", "监督管理"],
                success_factors=["制度保障", "全民参与"],
                applicable_conditions=["居民配合", "资源充足"],
                source="sample_cases"
            )
        ]
        
        # 创建测试政策参考（简化）
        test_policies = [
            PolicyReference(
                policy_id="test_policy_1",
                title="垃圾分类管理条例",
                admin_level="市级",
                relevance_score=0.9,
                key_provisions=["强制分类", "奖惩机制"],
                compliance_requirements=["依法执行", "规范管理"],
                implementation_guidance=["加强宣传", "完善设施"],
                source="policy_db"
            )
        ]
        
        # 生成解决方案
        print("生成解决方案测试...")
        solution_plan = generator.generate_solution(
            test_problem, test_cases, test_policies
        )
        
        print(f"✅ 解决方案生成成功")
        print(f"   步骤数量: {len(solution_plan.solution_steps)}")
        print(f"   成功指标: {len(solution_plan.success_metrics)}")
        print(f"   本地化建议: {len(solution_plan.local_adaptations)}")
        print(f"   生成时间: {solution_plan.generated_at}")
        
    except Exception as e:
        print(f"测试失败: {e}")
        import traceback
        traceback.print_exc()