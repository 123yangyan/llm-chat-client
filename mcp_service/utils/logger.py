"""
Logger Utils

提供日志记录功能的工具模块。
"""

import logging
from ..config.settings import MCPSettings

def setup_logger(name: str) -> logging.Logger:
    """
    设置并返回一个配置好的日志记录器

    Args:
        name (str): 日志记录器的名称

    Returns:
        logging.Logger: 配置好的日志记录器
    """
    # 创建日志记录器
    logger = logging.getLogger(name)
    
    # 设置日志级别
    logger.setLevel(MCPSettings.LOG_LEVEL)
    
    # 如果日志记录器已经有处理器，说明已经配置过，直接返回
    if logger.handlers:
        return logger
    
    # 创建控制台处理器
    console_handler = logging.StreamHandler()
    console_handler.setLevel(MCPSettings.LOG_LEVEL)
    
    # 设置日志格式
    formatter = logging.Formatter(
        fmt=MCPSettings.LOG_FORMAT,
        datefmt=MCPSettings.LOG_DATE_FORMAT
    )
    console_handler.setFormatter(formatter)
    
    # 添加处理器到日志记录器
    logger.addHandler(console_handler)
    
    return logger 