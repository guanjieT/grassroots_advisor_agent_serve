# 项目重构计划

## 当前问题
1. 根目录文件过多，包含大量demo和test文件
2. 文档和报告文件散落在根目录
3. 缺乏清晰的模块划分
4. 临时文件和实验性代码混杂

## 新的项目结构

```
grassroots-governance-agent/
├── README.md                    # 项目主文档
├── requirements.txt             # 依赖文件
├── .env.example                # 环境变量示例
├── .gitignore                  # Git忽略文件
├── main.py                     # 主启动脚本
├── config.py                   # 配置文件
│
├── src/                        # 源代码目录
│   ├── __init__.py
│   ├── api.py                  # FastAPI接口
│   ├── app.py                  # Streamlit应用
│   ├── governance_agent.py     # 主治理Agent
│   │
│   ├── agent/                  # Agent模块
│   │   ├── __init__.py
│   │   └── langgraph_agent.py
│   │
│   ├── core/                   # 核心业务逻辑
│   │   ├── __init__.py
│   │   ├── case_engine.py
│   │   ├── policy_engine.py
│   │   ├── solution_generator.py
│   │   └── evaluation_engine.py
│   │
│   ├── knowledge_base/         # 知识库模块
│   │   ├── __init__.py
│   │   ├── vector_store.py
│   │   ├── loader.py
│   │   ├── processors/
│   │   │   ├── __init__.py
│   │   │   ├── doc_processor.py
│   │   │   ├── policy_processor.py
│   │   │   └── multi_format_processor.py
│   │   └── systems/
│   │       ├── __init__.py
│   │       ├── policy_rag_system.py
│   │       └── case_driven_system.py
│   │
│   ├── rag/                    # RAG模块
│   │   ├── __init__.py
│   │   ├── chains.py
│   │   └── rules_aware_chains.py
│   │
│   └── utils/                  # 工具模块
│       ├── __init__.py
│       └── logger.py
│
├── tests/                      # 测试目录
│   ├── __init__.py
│   ├── test_governance_system.py
│   ├── test_policy_rag.py
│   └── integration/
│       ├── __init__.py
│       └── test_full_workflow.py
│
├── examples/                   # 示例和演示
│   ├── __init__.py
│   ├── demo_governance_agent.py
│   ├── demo_policy_qa.py
│   ├── demo_case_driven_solution.py
│   └── simple_case_driven_demo.py
│
├── scripts/                    # 脚本工具
│   ├── __init__.py
│   ├── optimize_policy_data.py
│   ├── run_data_optimization.py
│   └── data_usage_examples.py
│
├── docs/                       # 文档目录
│   ├── README.md
│   ├── API.md
│   ├── DEPLOYMENT.md
│   ├── reports/
│   │   ├── 案例驱动系统总结报告.md
│   │   ├── 数据优化总结.md
│   │   ├── 政策数据优化完成报告.md
│   │   └── 政策RAG系统构建完成报告.md
│   └── architecture/
│       ├── system_design.md
│       └── data_flow.md
│
└── data/                       # 数据目录
    ├── knowledge_base/
    ├── vectorstores/
    ├── processed/
    └── temp/
```

## 重构步骤
1. 创建新的目录结构
2. 移动源代码文件到src目录
3. 整理测试文件到tests目录
4. 移动示例文件到examples目录
5. 整理脚本到scripts目录
6. 整理文档到docs目录
7. 更新导入路径
8. 更新配置文件
9. 测试重构后的系统

## 预期效果
- 清晰的模块划分
- 更好的代码组织
- 便于维护和扩展
- 符合Python项目最佳实践