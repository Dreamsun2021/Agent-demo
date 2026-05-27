# logger.py
import logging
import sys

def setup_logger(name: str = "agent", level: int = logging.INFO) -> logging.Logger:
    """配置并返回一个日志记录器，同时输出到控制台和文件"""
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # 避免重复添加 handler（如果已经配置过）
    if logger.handlers:
        return logger

    # 日志格式：时间 [级别] 消息
    formatter = logging.Formatter('%(asctime)s [%(levelname)s] %(message)s')

    # 控制台处理器
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # 文件处理器（追加写入 agent.log）
    file_handler = logging.FileHandler("agent.log", encoding="utf-8")
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    return logger

# 全局默认 logger，其他模块直接 import 使用
logger = setup_logger()