"""
日志工具模块
"""
import logging
import sys
from typing import Optional
from config import config

def setup_logger(name: str = "grassroots_advisor", level: Optional[str] = None) -> logging.Logger:
    """
    设置日志记录器
    
    Args:
        name: 日志记录器名称
        level: 日志级别
    
    Returns:
        配置好的日志记录器
    """
    logger = logging.getLogger(name)
    
    # 如果已经配置过处理器，直接返回
    if logger.handlers:
        return logger
    
    # 设置日志级别
    log_level = level or config.LOG_LEVEL
    logger.setLevel(getattr(logging, log_level.upper()))
    
    # 创建控制台处理器
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(getattr(logging, log_level.upper()))
    
    # 创建格式化器
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    console_handler.setFormatter(formatter)
    
    # 添加处理器到日志记录器
    logger.addHandler(console_handler)
    
    return logger

# 创建默认日志记录器
logger = setup_logger() 