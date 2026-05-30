import logging
import sys
from pathlib import Path
from logging.handlers import RotatingFileHandler, TimedRotatingFileHandler
from datetime import datetime, timezone
from typing import Optional
import json
import traceback


# Create logs directory if it doesn't exist
LOG_DIR = Path("logs")
LOG_DIR.mkdir(exist_ok=True)


class JSONFormatter(logging.Formatter):
    
    def format(self, record: logging.LogRecord) -> str:
        log_data = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        
        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = {
                "type": record.exc_info[0].__name__ if record.exc_info[0] else None,
                "message": str(record.exc_info[1]) if record.exc_info[1] else None,
                "traceback": traceback.format_exception(*record.exc_info)
            }
        
        # Add extra fields
        if hasattr(record, "user_id"):
            log_data["user_id"] = record.user_id
        if hasattr(record, "request_id"):
            log_data["request_id"] = record.request_id
        if hasattr(record, "endpoint"):
            log_data["endpoint"] = record.endpoint
            
        return json.dumps(log_data)


class AppLogger:
    
    def __init__(self, name: str = "agri_ai"):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.INFO)
        
        # Prevent duplicate handlers
        if self.logger.handlers:
            return
            
        self._setup_handlers()
        
    
    def _setup_handlers(self):
        
        # Console Handler (human-readable)
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        console_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        console_handler.setFormatter(console_formatter)
        
        # File Handler - General Logs (rotating by size)
        file_handler = RotatingFileHandler(
            LOG_DIR / "app.log",
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=5
        )
        file_handler.setLevel(logging.INFO)
        file_handler.setFormatter(console_formatter)
        
        # File Handler - Error Logs (rotating by time)
        error_handler = TimedRotatingFileHandler(
            LOG_DIR / "error.log",
            when="midnight",
            interval=1,
            backupCount=30
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(JSONFormatter())
        
        # File Handler - JSON structured logs
        json_handler = RotatingFileHandler(
            LOG_DIR / "app.json",
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=5
        )
        json_handler.setLevel(logging.INFO)
        json_handler.setFormatter(JSONFormatter())
        
        # Add handlers
        self.logger.addHandler(console_handler)
        self.logger.addHandler(file_handler)
        self.logger.addHandler(error_handler)
        self.logger.addHandler(json_handler)
    
    def info(self, message: str, **kwargs):
        extra = self._build_extra(kwargs)
        self.logger.info(message, extra=extra)

    def debug(self, message: str, **kwargs):
        extra = self._build_extra(kwargs)
        self.logger.debug(message, extra=extra)
    
    def warning(self, message: str, **kwargs):
        extra = self._build_extra(kwargs)
        self.logger.warning(message, extra=extra)
    
    def error(self, message: str, exc_info: Optional[Exception] = None, **kwargs):
        extra = self._build_extra(kwargs)
        self.logger.error(message, exc_info=exc_info or sys.exc_info(), extra=extra)
    
    def critical(self, message: str, exc_info: Optional[Exception] = None, **kwargs):
        extra = self._build_extra(kwargs)
        self.logger.critical(message, exc_info=exc_info or sys.exc_info(), extra=extra)
    
    def _build_extra(self, kwargs: dict) -> dict:
        extra = {}
        if "user_id" in kwargs:
            extra["user_id"] = kwargs["user_id"]
        if "request_id" in kwargs:
            extra["request_id"] = kwargs["request_id"]
        if "endpoint" in kwargs:
            extra["endpoint"] = kwargs["endpoint"]
        return extra


# Global logger instance
logger = AppLogger()


# Helper function for easy import
def get_logger(name: str = "agri_ai") -> AppLogger:
    return AppLogger(name)
