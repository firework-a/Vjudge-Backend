from loguru import logger

def setup_logger():
    logger.add(
        "system.log",
        rotation="1 day",
        retention="7 days",
        encoding="utf-8",
        format="{message}"
    )
    return logger