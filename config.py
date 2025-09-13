"""
配置文件
管理应用的所有配置项
"""
import os
from typing import Optional
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

class Config:
    """应用配置类"""
    
    # DashScope 配置
    DASHSCOPE_API_KEY: str = os.getenv("DASHSCOPE_API_KEY", "")
    LLM_MODEL: str = os.getenv("DASHSCOPE_MODEL", "qwen-max")
    DASHSCOPE_TEMPERATURE: float = float(os.getenv("DASHSCOPE_TEMPERATURE", "0.7"))
    DASHSCOPE_MAX_TOKENS: int = int(os.getenv("DASHSCOPE_MAX_TOKENS", "2000"))
    
    # LangSmith 配置
    LANGSMITH_API_KEY: str = os.getenv("LANGSMITH_API_KEY", "")
    LANGCHAIN_TRACING_V2: bool = os.getenv("LANGCHAIN_TRACING_V2", "false").lower() == "true"
    LANGCHAIN_ENDPOINT: str = os.getenv("LANGCHAIN_ENDPOINT", "https://api.smith.langchain.com")
    LANGCHAIN_PROJECT: str = os.getenv("LANGCHAIN_PROJECT", "grassroots-advisor-agent")
    
    # 向量数据库配置
    CHROMA_PERSIST_DIRECTORY: str = os.getenv("CHROMA_PERSIST_DIRECTORY", "./data/chroma_db")
    EMBEDDING_MODEL: str = os.getenv("EMBEDDING_MODEL", "text-embedding-v3")
    
    # RAG 配置
    CHUNK_SIZE: int = int(os.getenv("CHUNK_SIZE", "1000"))
    CHUNK_OVERLAP: int = int(os.getenv("CHUNK_OVERLAP", "200"))
    RETRIEVAL_K: int = int(os.getenv("RETRIEVAL_K", "5"))
    SCORE_THRESHOLD: float = float(os.getenv("SCORE_THRESHOLD", "0.5"))
    
    # 应用配置
    APP_DEBUG: bool = os.getenv("APP_DEBUG", "false").lower() == "true"
    # 日志配置
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    
    # 知识库路径
    KNOWLEDGE_BASE_PATH: str = os.getenv("KNOWLEDGE_BASE_PATH", "./data/knowledge_base")
    
    @classmethod
    def validate_config(cls) -> bool:
        """验证配置是否完整"""
        if not cls.DASHSCOPE_API_KEY:
            raise ValueError("DASHSCOPE_API_KEY 未设置")
        return True

# 配置实例
config = Config()

# 验证配置
if __name__ == "__main__":
    try:
        config.validate_config()
        print("✅ 配置验证通过")
    except ValueError as e:
        print(f"❌ 配置错误: {e}") 