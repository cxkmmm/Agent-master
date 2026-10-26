import logging
import os
from datetime import datetime
from smart_agent.utils.path_tool import get_abs_path

# 日志保存目录
LOG_ROOT = get_abs_path("logs")

# 确保日志目录存在，如果不存在则创建
os.makedirs(LOG_ROOT, exist_ok=True)

# 日志格式配置
# asctime：记录时间
# name：日志记录器名称
# levelname：日志级别
# message：日志消息
DEFAULT_LOG_FORMAT = logging.Formatter(
    "%(asctime)s - %(name)s - %(levelname)s -%(filename)s:%(lineno)d %(message)s"
)

def get_logger(
    name:str='agent',
    level:int = logging.INFO,
    file_level:int = logging.DEBUG,
    log_file= None,

) -> logging.Logger:
    """
    获取日志记录器
    """
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)
    if logger.handlers:
        return logger
    
    # 创建控制台处理器
    console_handler = logging.StreamHandler()
    console_handler.setLevel(level)
    console_handler.setFormatter(DEFAULT_LOG_FORMAT)

    logger.addHandler(console_handler)
    
    # 创建文件处理器
    if not log_file:
        log_file = os.path.join(LOG_ROOT, f"{name}_{datetime.now().strftime('%Y%m%d')}.log")
    
    file_handler = logging.FileHandler(log_file, encoding='utf-8')  #如果文件不存在，会自动创建。
    file_handler.setLevel(file_level)
    file_handler.setFormatter(DEFAULT_LOG_FORMAT)

    logger.addHandler(file_handler)
    
    return logger

logger = get_logger()

if __name__ == "__main__":
    logger.info("这是一条info日志")
    logger.debug("这是一条debug日志")
    logger.error("这是一条error日志")
    logger.warning("这是一条warning日志")
    
    
