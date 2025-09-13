#!/usr/bin/env python3
"""
基层治理辅助Agent系统核心功能测试
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_system_initialization():
    """测试系统初始化"""
    print("🚀 测试系统初始化...")
    
    try:
        from src.governance_agent import GrassrootsGovernanceAgent
        
        agent = GrassrootsGovernanceAgent()
        status = agent.get_system_status()
        
        print(f"✅ 系统初始化成功")
        print(f"   初始化状态: {status['system_initialized']}")
        
        if status.get('statistics'):
            print(f"   案例库: {status['statistics'].get('total_cases', 0)} 个案例")
        
        return agent
        
    except Exception as e:
        print(f"❌ 系统初始化失败: {e}")
        return None

def test_problem_solving(agent):
    """测试问题解决功能"""
    print("\n🔍 测试问题解决功能...")
    
    test_problems = [
        {
            "problem_description": "社区老年人对智能手机使用困难，无法使用健康码等数字化服务",
            "location": "北京市朝阳区某社区",
            "urgency_level": 3,
            "stakeholders": ["社区老年人", "社区工作者", "志愿者"],
            "constraints": ["预算有限", "老年人学习能力有限"],
            "expected_outcome": "帮助老年人掌握基本数字化服务使用"
        },
        {
            "problem_description": "小区垃圾分类推行困难，居民参与度不高",
            "location": "上海市浦东新区某小区",
            "urgency_level": 4,
            "stakeholders": ["小区居民", "物业公司", "环卫部门"],
            "constraints": ["居民习惯难改", "监督成本高"],
            "expected_outcome": "提高垃圾分类参与率至80%以上"
        }
    ]
    
    for i, problem in enumerate(test_problems, 1):
        print(f"\n--- 测试问题 {i} ---")
        print(f"问题: {problem['problem_description'][:50]}...")
        
        try:
            result = agent.solve_governance_problem(**problem)
            
            if "error" not in result:
                print("✅ 问题解决成功")
                print(f"   参考案例: {len(result.get('case_references', []))} 个")
                print(f"   政策参考: {len(result.get('policy_references', []))} 个")
                print(f"   解决步骤: {len(result.get('solution_plan', {}).get('steps', []))} 步")
                
                # 显示评估结果
                evaluation = result.get('evaluation', {})
                if evaluation:
                    overall_score = evaluation.get('overall_score', 0)
                    print(f"   综合评分: {overall_score:.2f}/5.0")
            else:
                print(f"❌ 问题解决失败: {result['error']}")
                
        except Exception as e:
            print(f"❌ 问题解决异常: {e}")

def test_batch_processing(agent):
    """测试批量处理功能"""
    print("\n📊 测试批量处理功能...")
    
    batch_problems = [
        {
            "description": "邻里噪音纠纷频发",
            "location": "广州市天河区某小区",
            "urgency_level": 3,
            "stakeholders": ["居民", "物业"],
            "constraints": ["法律边界", "邻里关系"],
            "expected_outcome": "减少噪音投诉"
        },
        {
            "description": "老旧小区停车位不足",
            "location": "北京市海淀区某小区",
            "urgency_level": 4,
            "stakeholders": ["业主", "物业", "交管部门"],
            "constraints": ["空间有限", "改造成本高"],
            "expected_outcome": "规范停车秩序"
        }
    ]
    
    try:
        results = agent.batch_solve_problems(batch_problems)
        
        success_count = sum(1 for r in results if "error" not in r)
        print(f"✅ 批量处理完成: {success_count}/{len(results)} 成功")
        
        for i, result in enumerate(results, 1):
            if "error" not in result:
                print(f"   问题 {i}: 成功生成解决方案")
            else:
                print(f"   问题 {i}: 处理失败 - {result['error']}")
                
    except Exception as e:
        print(f"❌ 批量处理异常: {e}")

def test_solution_comparison(agent):
    """测试方案比较功能"""
    print("\n🔄 测试方案比较功能...")
    
    try:
        result = agent.compare_solutions(
            problem_description="社区环境卫生管理问题",
            location="深圳市南山区某社区",
            alternative_approaches=["志愿者管理", "专业保洁", "居民自治"]
        )
        
        if "error" not in result:
            print("✅ 方案比较成功")
            solutions_count = len(result.get("solutions", []))
            best_index = result.get("comparison_summary", {}).get("best_solution_index", 0)
            print(f"   生成方案数: {solutions_count}")
            print(f"   最佳方案索引: {best_index}")
        else:
            print(f"❌ 方案比较失败: {result['error']}")
            
    except Exception as e:
        print(f"❌ 方案比较异常: {e}")

def main():
    """主测试函数"""
    print("🏛️ 基层治理辅助Agent系统测试")
    print("=" * 50)
    
    # 测试系统初始化
    agent = test_system_initialization()
    
    if not agent:
        print("❌ 系统初始化失败，终止测试")
        return
    
    # 测试核心功能
    test_problem_solving(agent)
    test_batch_processing(agent)
    test_solution_comparison(agent)
    
    print("\n🎉 测试完成!")

if __name__ == "__main__":
    main()