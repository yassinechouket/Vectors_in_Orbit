import logging
import sys
from pathlib import Path
from datetime import datetime
from utils.constants import DEFAULT_PATHS
import os


class Logger:
    """Simple centralized logger for all OnBoard components."""
    
    _loggers = {}
    _log_dir = None
    
    @classmethod
    def _get_log_dir(cls) -> Path:
        """Get or create the logs directory at project root."""
        if cls._log_dir is None:
            cls._log_dir = Path(DEFAULT_PATHS["logs"])
            os.makedirs(cls._log_dir, exist_ok=True)
        return cls._log_dir
    
    @classmethod
    def _get_log_file(cls) -> Path:
        """Get today's log file path."""
        log_dir = cls._get_log_dir()
        today = datetime.now().strftime("%Y-%m-%d")
        os.makedirs(log_dir, exist_ok=True)
        return log_dir / f"{today}.log"
    
    @classmethod
    def get_logger(cls, name: str) -> logging.Logger:
        """
        Get or create a logger with the specified name.
        
        Args:
            name: Logger name (typically module name like 'apis.cv_rewriter')
        
        Returns:
            Configured logger instance
        """
        if name in cls._loggers:
            return cls._loggers[name]
        
        logger = logging.getLogger(name)
        logger.setLevel(logging.DEBUG)
        
        # Remove existing handlers to avoid duplicates
        logger.handlers.clear()
        
        # Custom formatter: timestamp - [LEVEL] => message
        formatter = logging.Formatter(
            fmt='%(asctime)s - [%(levelname)s] => %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # Console handler (stdout)
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
        
        # File handler (daily log file)
        try:
            log_file = cls._get_log_file()
            file_handler = logging.FileHandler(log_file, encoding='utf-8')
            file_handler.setLevel(logging.DEBUG)
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)
        except Exception as e:
            # Fallback: log to console only if file logging fails
            logger.warning(f"Could not create file handler: {e}")
        
        # Prevent propagation to root logger
        logger.propagate = False
        
        cls._loggers[name] = logger
        return logger


# Convenience function for easy imports
def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance.
    
    Usage:
        from shared.helpers.logger import get_logger
        logger = get_logger(__name__)
        logger.info("Processing CV...")
    
    Args:
        name: Logger name (use __name__ for automatic module naming)
    
    Returns:
        Configured logger instance
    """
    return Logger.get_logger(name)
