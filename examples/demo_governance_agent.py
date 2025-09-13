#!/usr/bin/env python3
"""
基层治理辅助Agent演示程序
展示系统的核心功能和使用方法
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def demo_basic_usage():
    """演示基本使用方法"""
    print("🏛️ 基层治理辅助Agent演示")
    print("=" * 50)
    
    try:
        from src.governance_agent import GrassrootsGovernanceAgent
        
        # 初始化系统
        print("1. 初始化治理Agent...")
        agent = GrassrootsGovernanceAgent()
        
        # 获取系统状态
        print("2. 检查系统状态...")
        status = agent.get_system_status()
        print(f"   系统初始化: {status.get('system_initialized', False)}")
        
        # 演示问题解决
        print("\n3. 演示问题解决...")
        demo_problem = {
            "problem_description": "社区老年人数字鸿沟问题严重，很多老人不会使用智能手机和各种APP，影响日常生活便利性",
            "location": "北京市朝阳区望京街道某社区",
            "urgency_level": 3,
            "stakeholders": ["社区老年人", "社区工作者", "志愿者", "家属"],
            "constraints": ["老年人学习能力有限", "培训资源不足", "设备操作复杂"],
            "expected_outcome": "帮助老年人掌握基本智能手机使用技能，能够独立使用健康码、支付宝等常用功能"
        }
        
        print(f"   问题描述: {demo_problem['problem_description'][:60]}...")
        print(f"   地区位置: {demo_problem['location']}")
        print(f"   紧急程度: {demo_problem['urgency_level']}/5")
        
        result = agent.solve_governance_problem(**demo_problem)
        
        if "error" not in result:
            print("\n✅ 解决方案生成成功!")
            
            # 显示解决方案概要
            solution_plan = result.get("solution_plan", {})
            steps = solution_plan.get("steps", [])
            
            print(f"\n📋 解决方案概要:")
            print(f"   实施步骤: {len(steps)} 步")
            
            for i, step in enumerate(steps[:3], 1):  # 只显示前3步
                if isinstance(step, dict):
                    step_title = step.get("title", f"步骤 {i}")
                    print(f"   {i}. {step_title}")
                else:
                    print(f"   {i}. {step}")
            
            if len(steps) > 3:
                print(f"   ... 还有 {len(steps) - 3} 个步骤")
            
            # 显示参考案例
            case_refs = result.get("case_references", [])
            print(f"\n📚 参考案例: {len(case_refs)} 个")
            for i, case in enumerate(case_refs[:2], 1):
                print(f"   {i}. {case.get('title', '未知标题')} (相似度: {case.get('similarity_score', 0):.2f})")
            
            # 显示政策参考
            policy_refs = result.get("policy_references", [])
            print(f"\n📜 政策参考: {len(policy_refs)} 个")
            for i, policy in enumerate(policy_refs[:2], 1):
                print(f"   {i}. {policy.get('title', '未知标题')} (相关度: {policy.get('relevance_score', 0):.2f})")
            
            # 显示评估结果
            evaluation = result.get("evaluation", {})
            if evaluation:
                overall_score = evaluation.get("overall_score", 0)
                print(f"\n📊 方案评估: {overall_score:.2f}/5.0")
                
                dimensions = evaluation.get("dimension_scores", {})
                if dimensions:
                    print("   各维度评分:")
                    for dim, score in dimensions.items():
                        print(f"     {dim}: {score:.2f}")
        
        else:
            print(f"❌ 解决方案生成失败: {result['error']}")
        
        print("\n🎉 演示完成!")
        
    except Exception as e:
        print(f"❌ 演示过程出现错误: {e}")
        import traceback
        traceback.print_exc()

def demo_interactive_mode():
    """交互式演示模式"""
    print("\n🔄 进入交互式演示模式")
    print("您可以输入自己的治理问题，系统将为您生成解决方案")
    print("输入 'quit' 退出")
    
    try:
        from src.governance_agent import GrassrootsGovernanceAgent
        agent = GrassrootsGovernanceAgent()
        
        while True:
            print("\n" + "-" * 50)
            problem_desc = input("请描述您遇到的治理问题: ").strip()
            
            if problem_desc.lower() == 'quit':
                break
            
            if not problem_desc:
                print("请输入有效的问题描述")
                continue
            
            location = input("请输入地区位置 (可选): ").strip() or "某地区"
            
            try:
                urgency = int(input("请输入紧急程度 (1-5, 默认3): ").strip() or "3")
                urgency = max(1, min(5, urgency))
            except ValueError:
                urgency = 3
            
            print(f"\n🔍 正在为您生成解决方案...")
            
            result = agent.solve_governance_problem(
                problem_description=problem_desc,
                location=location,
                urgency_level=urgency
            )
            
            if "error" not in result:
                print("✅ 解决方案生成成功!")
                
                solution_plan = result.get("solution_plan", {})
                steps = solution_plan.get("steps", [])
                
                print(f"\n💡 推荐解决方案:")
                for i, step in enumerate(steps, 1):
                    if isinstance(step, dict):
                        step_title = step.get("title", f"步骤 {i}")
                        step_desc = step.get("description", "")
                        print(f"{i}. {step_title}")
                        if step_desc:
                            print(f"   {step_desc}")
                    else:
                        print(f"{i}. {step}")
                
                # 显示评估分数
                evaluation = result.get("evaluation", {})
                if evaluation:
                    overall_score = evaluation.get("overall_score", 0)
                    print(f"\n📊 方案评分: {overall_score:.2f}/5.0")
            
            else:
                print(f"❌ 生成失败: {result['error']}")
        
        print("\n👋 感谢使用基层治理辅助Agent!")
        
    except Exception as e:
        print(f"❌ 交互模式出现错误: {e}")

def main():
    """主函数"""
    print("欢迎使用基层治理辅助Agent演示程序!")
    print("请选择演示模式:")
    print("1. 基本功能演示")
    print("2. 交互式演示")
    
    try:
        choice = input("请输入选择 (1 或 2): ").strip()
        
        if choice == "1":
            demo_basic_usage()
        elif choice == "2":
            demo_interactive_mode()
        else:
            print("无效选择，运行基本功能演示")
            demo_basic_usage()
            
    except KeyboardInterrupt:
        print("\n\n👋 演示已取消")
    except Exception as e:
        print(f"❌ 程序出现错误: {e}")

if __name__ == "__main__":
    main()