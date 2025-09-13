#!/usr/bin/env python3
"""
基层工作智能辅助Agent - 主启动脚本
"""

import argparse
import sys
import os
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def run_streamlit():
    """启动Streamlit应用"""
    import subprocess
    print("🚀 启动Streamlit Web应用...")
    print("📍 访问地址: http://localhost:8501")
    subprocess.run([sys.executable, "-m", "streamlit", "run", "src/app.py"])

def run_fastapi():
    """启动FastAPI应用"""
    import subprocess
    print("🚀 启动FastAPI应用...")
    print("📍 API文档: http://localhost:8000/docs")
    subprocess.run([sys.executable, "api.py"])

def build_knowledge_base():
    """构建知识库"""
    print("🏗️ 构建知识库...")
    try:
        from src.knowledge_base.vector_store import build_knowledge_base
        
        # 询问是否包含法规政策数据
        include_rules = input("是否包含法规政策数据？(y/n, 默认y): ").lower()
        include_rules = include_rules != 'n'
        
        if include_rules:
            print("📚 将包含法规政策数据，这可能需要较长时间...")
        
        success = build_knowledge_base(include_rules=include_rules)
        if success:
            print("✅ 知识库构建成功!")
        else:
            print("❌ 知识库构建失败!")
    except Exception as e:
        print(f"❌ 知识库构建出错: {e}")

def test_agent():
    """测试Agent功能"""
    print("🧪 测试Agent功能...")
    try:
        from src.agent.langgraph_agent import GrassrootsAdvisorAgent
        from src.governance_agent import GrassrootsGovernanceAgent
        
        # 测试普通模式
        print("\n--- 测试普通模式 ---")
        agent = GrassrootsAdvisorAgent(use_rules=False)
        test_question = "如何处理邻里纠纷？"
        
        print(f"测试问题: {test_question}")
        answer = agent.get_simple_answer(test_question)
        
        print("✅ 普通模式测试成功!")
        print(f"回答预览: {answer[:200]}...")
        
        # 测试法规感知模式
        print("\n--- 测试法规感知模式 ---")
        rules_agent = GrassrootsAdvisorAgent(use_rules=True)
        rules_answer = rules_agent.get_simple_answer(test_question)
        
        print("✅ 法规感知模式测试成功!")
        print(f"回答预览: {rules_answer[:200]}...")
        
        # 测试治理Agent
        print("\n--- 测试治理Agent ---")
        governance_agent = GrassrootsGovernanceAgent()
        
        test_problem = {
            "problem_description": "社区老年人对智能手机使用困难，无法使用健康码等数字化服务",
            "location": "北京市朝阳区某社区",
            "urgency_level": 3,
            "stakeholders": ["社区老年人", "社区工作者", "志愿者"],
            "constraints": ["预算有限", "老年人学习能力有限"],
            "expected_outcome": "帮助老年人掌握基本数字化服务使用"
        }
        
        print(f"测试治理问题: {test_problem['problem_description']}")
        result = governance_agent.solve_governance_problem(**test_problem)
        
        if "error" not in result:
            print("✅ 治理Agent测试成功!")
            print(f"解决方案预览: {str(result.get('solution_plan', {}))[:200]}...")
            print(f"参考案例数量: {len(result.get('case_references', []))}")
            print(f"政策参考数量: {len(result.get('policy_references', []))}")
        else:
            print(f"❌ 治理Agent测试失败: {result['error']}")
        
    except Exception as e:
        print(f"❌ Agent测试失败: {e}")

def process_rules():
    """处理法规政策文件"""
    print("📚 处理法规政策文件...")
    try:
        from src.knowledge_base.rules_processor import RulesProcessor
        
        processor = RulesProcessor()
        documents = processor.create_rules_knowledge_base()
        
        if documents:
            print(f"✅ 成功处理 {len(documents)} 个法规政策文档!")
            
            # 统计不同类型的文档
            doc_types = {}
            for doc in documents:
                doc_type = doc.metadata.get('type', 'unknown')
                doc_types[doc_type] = doc_types.get(doc_type, 0) + 1
            
            print("文档类型统计:")
            for doc_type, count in doc_types.items():
                print(f"  {doc_type}: {count} 个")
        else:
            print("❌ 法规政策文件处理失败!")
            
    except Exception as e:
        print(f"❌ 法规政策处理出错: {e}")

def test_governance_agent():
    """专门测试治理Agent功能"""
    print("🏛️ 测试治理Agent功能...")
    try:
        from src.governance_agent import GrassrootsGovernanceAgent
        
        # 创建治理Agent实例
        print("初始化治理Agent...")
        governance_agent = GrassrootsGovernanceAgent()
        
        # 获取系统状态
        print("\n--- 系统状态检查 ---")
        status = governance_agent.get_system_status()
        if "error" not in status:
            print("✅ 系统状态正常")
            print(f"系统初始化: {status.get('system_initialized', False)}")
            print(f"子系统状态: {list(status.get('subsystems', {}).keys())}")
        else:
            print(f"❌ 系统状态异常: {status['error']}")
        
        # 测试单个问题解决
        print("\n--- 单个问题解决测试 ---")
        test_problems = [
            {
                "problem_description": "社区垃圾分类推行困难，居民参与度不高",
                "location": "上海市浦东新区某社区",
                "urgency_level": 3,
                "stakeholders": ["社区居民", "物业公司", "环卫部门"],
                "constraints": ["居民习惯难改", "监督成本高"],
                "expected_outcome": "提高垃圾分类参与率至80%以上"
            },
            {
                "problem_description": "老旧小区停车位不足，车辆乱停乱放现象严重",
                "location": "北京市海淀区某老旧小区",
                "urgency_level": 4,
                "stakeholders": ["业主", "物业", "交管部门"],
                "constraints": ["空间有限", "改造成本高"],
                "expected_outcome": "规范停车秩序，减少停车纠纷"
            }
        ]
        
        for i, problem in enumerate(test_problems, 1):
            print(f"\n测试问题 {i}: {problem['problem_description'][:30]}...")
            result = governance_agent.solve_governance_problem(**problem)
            
            if "error" not in result:
                print(f"✅ 问题 {i} 解决方案生成成功")
                print(f"   - 参考案例: {len(result.get('case_references', []))} 个")
                print(f"   - 政策参考: {len(result.get('policy_references', []))} 个")
                print(f"   - 解决步骤: {len(result.get('solution_plan', {}).get('steps', []))} 步")
                
                # 显示评估结果
                evaluation = result.get('evaluation', {})
                if evaluation:
                    overall_score = evaluation.get('overall_score', 0)
                    print(f"   - 综合评分: {overall_score:.2f}/5.0")
            else:
                print(f"❌ 问题 {i} 处理失败: {result['error']}")
        
        # 测试批量处理
        print("\n--- 批量处理测试 ---")
        batch_results = governance_agent.batch_solve_problems(test_problems)
        success_count = sum(1 for r in batch_results if "error" not in r)
        print(f"✅ 批量处理完成: {success_count}/{len(batch_results)} 成功")
        
        # 测试方案比较
        print("\n--- 方案比较测试 ---")
        comparison_result = governance_agent.compare_solutions(
            problem_description="社区噪音扰民问题严重",
            location="广州市天河区某社区",
            alternative_approaches=["调解协商", "技术改造", "制度约束"]
        )
        
        if "error" not in comparison_result:
            print("✅ 方案比较功能正常")
            solutions_count = len(comparison_result.get("solutions", []))
            best_index = comparison_result.get("comparison_summary", {}).get("best_solution_index", 0)
            print(f"   - 生成方案数: {solutions_count}")
            print(f"   - 最佳方案索引: {best_index}")
        else:
            print(f"❌ 方案比较失败: {comparison_result['error']}")
        
        print("\n🎉 治理Agent功能测试完成!")
        
    except Exception as e:
        print(f"❌ 治理Agent测试失败: {e}")
        import traceback
        traceback.print_exc()

def check_environment():
    """检查环境配置"""
    print("🔍 检查环境配置...")
    
    try:
        from config import config
        
        checks = [
            ("DashScope API Key", bool(config.DASHSCOPE_API_KEY)),
            ("LangSmith API Key", bool(config.LANGSMITH_API_KEY)),
            ("知识库路径", os.path.exists(config.KNOWLEDGE_BASE_PATH)),
            ("ChromaDB目录", os.path.exists(os.path.dirname(config.CHROMA_PERSIST_DIRECTORY)))
        ]
        
        print("\n配置检查结果:")
        for item, status in checks:
            status_icon = "✅" if status else "❌"
            print(f"{status_icon} {item}: {'正常' if status else '需要配置'}")
        
        # 创建必要目录
        os.makedirs(config.KNOWLEDGE_BASE_PATH, exist_ok=True)
        os.makedirs(config.CHROMA_PERSIST_DIRECTORY, exist_ok=True)
        
        return all(status for _, status in checks[:2])  # API Keys是必需的
        
    except Exception as e:
        print(f"❌ 环境检查失败: {e}")
        return False

def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="基层工作智能辅助Agent",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
  python main.py web          # 启动Web界面
  python main.py api          # 启动API服务
  python main.py build        # 构建知识库
  python main.py test         # 测试Agent
  python main.py check        # 检查环境
  python main.py rules        # 处理法规政策文件
  python main.py governance   # 测试治理Agent功能
        """
    )
    
    parser.add_argument(
        "command",
        choices=["web", "api", "build", "test", "check", "rules", "governance"],
        help="要执行的命令"
    )
    
    args = parser.parse_args()
    
    print("🏢 基层工作智能辅助Agent")
    print("=" * 50)
    
    # 首先检查环境
    if args.command != "check":
        if not check_environment():
            print("\n⚠️ 环境配置不完整，请先配置API密钥")
            print("💡 提示: 复制 env_example.txt 为 .env 并填入API密钥")
            return
    
    print()
    
    # 执行对应命令
    if args.command == "web":
        run_streamlit()
    elif args.command == "api":
        run_fastapi()
    elif args.command == "build":
        build_knowledge_base()
    elif args.command == "test":
        test_agent()
    elif args.command == "check":
        check_environment()
    elif args.command == "rules":
        process_rules()
    elif args.command == "governance":
        test_governance_agent()

if __name__ == "__main__":
    main() 