import os
import sys
from pathlib import Path

import langchain
from loguru import logger

sys.path.append(Path(__file__).parents[2].as_posix())
from configs import config

logger.remove()

# 是否显示详细日志
log_verbose = True
langchain.verbose = True


class Logger:

    def __init__(self):

        # 日志存储路径
        LOG_PATH = Path(__file__).parents[2] / "logs"
        if not os.path.exists(LOG_PATH):
            os.mkdir(LOG_PATH)

        # 日志格式
        LOG_FORMAT = "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | <level>{level: <8}</level> | <cyan>{file}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>"

        logger.add(
            sink=sys.stderr,
            level=config.constant.console_level,
            format=LOG_FORMAT,
            backtrace=True,
            diagnose=True,
        )
        logger.add(
            sink=LOG_PATH / "KEngine.log",
            level=config.constant.file_level,
            format=LOG_FORMAT,
            rotation="500 MB",
            colorize=False,
            encoding="utf-8",
            backtrace=True,
            diagnose=True,
        )  # 文件输出，文件大小超过50MB时滚动
        self.logger = logger


logger = Logger().logger

if __name__ == "__main__":
    logger.trace("Trace message")
    logger.debug("Debug message")
    logger.info("Info message")
    logger.warning("Warning message")
    logger.error("Error message")
    logger.critical("Critical message")
