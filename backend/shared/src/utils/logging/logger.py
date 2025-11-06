import logging
import os

def get_logger(name=None):
    """Get a logger instance for the specified service"""
    if name is None:
        name = os.getenv("SERVICE_NAME", "bsw-service")
    
    logger = logging.getLogger(name)
    
    # Only configure if not already configured
    if not logger.handlers:
        formatter = logging.Formatter("%(levelname)s - %(filename)s - %(message)s")
        logger.setLevel(os.getenv("LOG_LEVEL", "INFO").upper())

        handler = logging.StreamHandler()
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        
        logger.propagate = False
    
    return logger

# Default logger instance
logger = get_logger()