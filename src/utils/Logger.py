import os
import sys
from pathlib import Path

import langchain
from loguru import logger
from functools import partial
sys.path.append(Path(__file__).parents[2].as_posix())
from configs import config

logger.remove()

# 是否显示详细日志
log_verbose = True
langchain.verbose = True

def filter_function(appid, record):
    record["file"].path = (
        record["file"].path.split(f"{appid}/")[1] if f"{appid}/" in record["file"].path else record["file"].path
    )
    return True
    
class Logger:
    def __init__(self, appid):
        LOG_PATH = Path(__file__).parents[2] / "logs"
        if not os.path.exists(LOG_PATH):
            os.mkdir(LOG_PATH)

        LOG_FORMAT = "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | <level>{level: <8}</level> | <cyan>{file.path}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>"

        logger.add(
            sink=sys.stderr,
            level=config.constant.console_level,
            format=LOG_FORMAT,
            backtrace=True,
            diagnose=True,
            filter=partial(filter_function, appid),
        )
        logger.add(
            sink=LOG_PATH / f"{appid}.log",
            level=config.constant.file_level,
            format=LOG_FORMAT,
            rotation="50 MB",
            colorize=False,
            encoding="utf-8",
            backtrace=True,
            diagnose=True,
        )
        self.logger = logger


logger = Logger("KEngine").logger

if __name__ == "__main__":
    logger.trace("Trace message")
    logger.debug("Debug message")
    logger.info("Info message")
    logger.warning("Warning message")
    logger.error("Error message")
    logger.critical("Critical message")
