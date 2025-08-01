# hive/utils/logging_config.py

import logging
import sys
import os
from logging.handlers import RotatingFileHandler

def setup_logging():
    """
    配置全局日志记录。
    此函数设置了一个双通道的日志系统：
    1. 控制台 (StreamHandler): 输出INFO及以上级别的日志，便于在开发时实时查看。
    2. 文件 (RotatingFileHandler): 在项目根目录下创建hive.log文件，
       记录DEBUG及以上级别的所有日志，用于详细的问题追溯和分析。
       日志文件达到5MB时会自动轮替，最多保留3个备份文件。
    """
    # 获取项目的根目录
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    log_file_path = os.path.join(project_root, 'hive.log')

    # 定义日志格式
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - [%(levelname)s] - %(message)s (%(filename)s:%(lineno)d)'
    )

    # 获取根logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)  # 设置根logger的最低级别为DEBUG

    # --- 配置控制台Handler ---
    # 避免重复添加handler
    if not any(isinstance(h, logging.StreamHandler) for h in root_logger.handlers):
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)  # 控制台只显示INFO及以上信息
        console_handler.setFormatter(formatter)
        root_logger.addHandler(console_handler)

    # --- 配置文件Handler ---
    # 避免重复添加handler
    if not any(isinstance(h, RotatingFileHandler) for h in root_logger.handlers):
        file_handler = RotatingFileHandler(
            log_file_path,
            maxBytes=5*1024*1024,  # 5 MB
            backupCount=3,
            encoding='utf-8'
        )
        file_handler.setLevel(logging.DEBUG)  # 文件记录所有DEBUG及以上信息
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)

    logging.info("="*50)
    logging.info("日志系统配置完成。输出将同时发送到控制台和hive.log文件。")
    logging.info(f"日志文件路径: {log_file_path}")
    logging.info("="*50)

if __name__ == '__main__':
    # 简单的自测试
    setup_logging()
    logging.debug("这是一条DEBUG级别的日志，应该只出现在文件中。")
    logging.info("这是一条INFO级别的日志，应该会出现在控制台和文件中。")
    logging.warning("这是一条WARNING级别的日志。")
    logging.error("这是一条ERROR级别的日志。")
    logging.critical("这是一条CRITICAL级别的日志。")