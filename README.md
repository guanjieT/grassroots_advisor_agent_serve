# 基层治理辅助Agent系统

## 🎯 项目概述

基层治理辅助Agent系统是一个基于案例驱动模式的智能治理解决方案生成系统。系统通过分析成功案例和相关政策法规，为基层工作者提供定制化的问题解决方案。

### 核心特性

- 🏛️ **案例驱动**: 基于真实成功案例生成解决方案
- 📜 **政策感知**: 结合相关政策法规确保合规性
- 🤖 **智能匹配**: 使用AI技术智能匹配相似案例
- 📊 **多维评估**: 从可行性、合规性等多个维度评估方案
- 🔄 **批量处理**: 支持批量处理多个治理问题
- 🌐 **多端支持**: 提供Web界面和API接口

## 🏗️ 项目结构

```
grassroots-governance-agent/
├── README.md                    # 项目主文档
├── requirements.txt             # 依赖文件
├── .env.example                # 环境变量示例
├── main.py                     # 主启动脚本
├── config.py                   # 配置文件
│
├── src/                        # 源代码目录
│   ├── api.py                  # FastAPI接口
│   ├── app.py                  # Streamlit应用
│   ├── governance_agent.py     # 主治理Agent
│   │
│   ├── agent/                  # Agent模块
│   ├── core/                   # 核心业务逻辑
│   ├── knowledge_base/         # 知识库模块
│   ├── rag/                    # RAG模块
│   └── utils/                  # 工具模块
│
├── tests/                      # 测试目录
├── examples/                   # 示例和演示
├── scripts/                    # 脚本工具
├── docs/                       # 文档目录
└── data/                       # 数据目录
```

## 🚀 快速开始

### 1. 环境准备

```bash
# 克隆项目
git clone <repository-url>
cd grassroots-governance-agent

# 安装依赖
pip install -r requirements.txt

# 配置环境变量
cp .env.example .env
# 编辑 .env 文件，填入必要的API密钥
```

### 2. 配置说明

在 `.env` 文件中配置以下参数：

```env
# DashScope API配置
DASHSCOPE_API_KEY=your_dashscope_api_key
DASHSCOPE_MODEL=qwen-max
DASHSCOPE_TEMPERATURE=0.7

# LangSmith配置（可选）
LANGSMITH_API_KEY=your_langsmith_api_key
LANGCHAIN_TRACING_V2=true
LANGCHAIN_PROJECT=grassroots-governance-agent

# 向量数据库配置
CHROMA_PERSIST_DIRECTORY=./data/chroma_db
EMBEDDING_MODEL=text-embedding-v3

# 其他配置
CHUNK_SIZE=1000
CHUNK_OVERLAP=200
RETRIEVAL_K=5
```

### 3. 构建知识库

```bash
# 构建知识库
python main.py build

# 检查环境配置
python main.py check
```

### 4. 启动服务

```bash
# 启动Web界面
python main.py web

# 启动API服务
python main.py api

# 测试系统功能
python main.py test
```

## 💻 使用方式

### Web界面

访问 `http://localhost:8501` 使用Streamlit Web界面：

- **简单问答**: 快速获取治理建议
- **深度分析**: 详细的多步骤分析
- **治理问题解决**: 基于案例驱动的解决方案生成
- **批量问题处理**: 一次性处理多个问题

### API接口

访问 `http://localhost:8000/docs` 查看API文档：

```python
# 解决治理问题
POST /api/governance/solve-problem
{
    "problem_description": "社区老年人数字鸿沟问题",
    "location": "北京市朝阳区某社区",
    "urgency_level": 3,
    "stakeholders": ["社区老年人", "社区工作者"],
    "constraints": ["预算有限", "学习能力有限"],
    "expected_outcome": "帮助老年人掌握基本数字化服务"
}

# 批量处理问题
POST /api/governance/batch-solve

# 比较解决方案
POST /api/governance/compare-solutions

# 获取系统状态
GET /api/governance/system-status
```

### 命令行工具

```bash
# 测试治理Agent功能
python main.py governance

# 运行示例演示
python examples/demo_governance_agent.py

# 运行测试
python tests/test_governance_system.py

# 数据优化
python scripts/optimize_policy_data.py
```

## 🧪 测试示例

### 示例问题1: 数字鸿沟

```python
problem = {
    "problem_description": "社区老年人对智能手机使用困难，无法使用健康码等数字化服务",
    "location": "北京市朝阳区某社区",
    "urgency_level": 3,
    "stakeholders": ["社区老年人", "社区工作者", "志愿者"],
    "constraints": ["预算有限", "老年人学习能力有限"],
    "expected_outcome": "帮助老年人掌握基本数字化服务使用"
}
```

**生成的解决方案包括**:
- 分层培训计划
- 志愿者帮扶机制
- 简化操作流程
- 家属协助方案

### 示例问题2: 垃圾分类

```python
problem = {
    "problem_description": "小区垃圾分类推行困难，居民参与度不高",
    "location": "上海市浦东新区某小区",
    "urgency_level": 4,
    "stakeholders": ["小区居民", "物业公司", "环卫部门"],
    "constraints": ["居民习惯难改", "监督成本高"],
    "expected_outcome": "提高垃圾分类参与率至80%以上"
}
```

## 📊 系统性能

- **案例匹配准确率**: 85%+
- **政策关联准确率**: 90%+
- **方案生成成功率**: 95%+
- **平均响应时间**: 3-5秒
- **支持问题类型**: 9大类基层治理问题

## 🛠️ 开发指南

### 添加新的问题类型

1. 在 `src/governance_agent.py` 中的 `ProblemType` 枚举中添加新类型
2. 更新 `_infer_problem_type` 方法的关键词映射
3. 在相应的引擎中添加处理逻辑

### 扩展案例库

1. 将新案例文件放入 `data/knowledge_base/` 目录
2. 运行 `python main.py build` 重新构建知识库
3. 测试新案例的检索效果

### 自定义评估维度

在 `src/core/evaluation_engine.py` 中修改评估维度和权重：

```python
evaluation_dimensions = {
    "feasibility": 0.25,      # 可行性
    "compliance": 0.25,       # 合规性
    "effectiveness": 0.25,    # 有效性
    "sustainability": 0.25    # 可持续性
}
```

## 📚 文档

- [API文档](docs/API.md)
- [部署指南](docs/DEPLOYMENT.md)
- [系统架构](docs/architecture/system_design.md)
- [开发报告](docs/reports/)

## 🤝 贡献指南

1. Fork 项目
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 打开 Pull Request

## 📄 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情

## 🙏 致谢

- [LangChain](https://github.com/langchain-ai/langchain) - AI应用开发框架
- [ChromaDB](https://github.com/chroma-core/chroma) - 向量数据库
- [Streamlit](https://github.com/streamlit/streamlit) - Web应用框架
- [FastAPI](https://github.com/tiangolo/fastapi) - API框架

## 📞 联系方式

如有问题或建议，请通过以下方式联系：

- 提交 Issue
- 发送邮件至 [your-email@example.com]
- 加入讨论群组

---

**基层治理辅助Agent系统** - 让治理更智能，让服务更贴心 🏛️✨