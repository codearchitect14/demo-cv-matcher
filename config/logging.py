import logging
import logging.config
import sys
from pathlib import Path
from datetime import datetime

def setup_logging():
    """Setup comprehensive logging configuration"""
    
    # Create logs directory
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    # Logging configuration
    logging_config = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "detailed": {
                "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                "datefmt": "%Y-%m-%d %H:%M:%S"
            },
            "simple": {
                "format": "%(levelname)s - %(message)s"
            },
            "json": {
                "format": '{"timestamp": "%(asctime)s", "level": "%(levelname)s", "logger": "%(name)s", "message": "%(message)s"}',
                "datefmt": "%Y-%m-%d %H:%M:%S"
            }
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "level": "INFO",
                "formatter": "simple",
                "stream": sys.stdout
            },
            "file": {
                "class": "logging.handlers.RotatingFileHandler",
                "level": "DEBUG",
                "formatter": "detailed",
                "filename": "logs/app.log",
                "maxBytes": 10485760,  # 10MB
                "backupCount": 5
            },
            "error_file": {
                "class": "logging.handlers.RotatingFileHandler",
                "level": "ERROR",
                "formatter": "detailed",
                "filename": "logs/error.log",
                "maxBytes": 10485760,  # 10MB
                "backupCount": 5
            },
            "api_file": {
                "class": "logging.handlers.RotatingFileHandler",
                "level": "INFO",
                "formatter": "json",
                "filename": "logs/api.log",
                "maxBytes": 10485760,  # 10MB
                "backupCount": 3
            }
        },
        "loggers": {
            "": {  # Root logger
                "handlers": ["console", "file"],
                "level": "INFO",
                "propagate": False
            },
            "api": {  # API logger
                "handlers": ["console", "api_file"],
                "level": "INFO",
                "propagate": False
            },
            "db": {  # Database logger
                "handlers": ["console", "file"],
                "level": "DEBUG",
                "propagate": False
            },
            "ml": {  # ML services logger
                "handlers": ["console", "file"],
                "level": "INFO",
                "propagate": False
            },
            "security": {  # Security logger
                "handlers": ["console", "error_file"],
                "level": "WARNING",
                "propagate": False
            }
        }
    }
    
    # Apply configuration
    logging.config.dictConfig(logging_config)
    
    # Create loggers
    api_logger = logging.getLogger("api")
    db_logger = logging.getLogger("db")
    ml_logger = logging.getLogger("ml")
    security_logger = logging.getLogger("security")
    
    return {
        "api": api_logger,
        "db": db_logger,
        "ml": ml_logger,
        "security": security_logger
    }

# Setup logging on import
loggers = setup_logging()

def get_logger(name: str) -> logging.Logger:
    """Get a logger with the specified name"""
    return logging.getLogger(name)

def log_api_request(request, response, duration: float):
    """Log API request/response"""
    logger = get_logger("api")
    
    # Extract information from FastAPI objects
    method = getattr(request, 'method', 'UNKNOWN')
    path = getattr(request, 'url', 'UNKNOWN')
    status_code = getattr(response, 'status_code', 'UNKNOWN')
    
    logger.info(
        f"API Request: {method} {path} "
        f"- Status: {status_code} "
        f"- Duration: {duration:.3f}s"
    )

def log_security_event(event: str, details: dict):
    """Log security events"""
    logger = get_logger("security")
    logger.warning(f"Security Event: {event} - Details: {details}")

def log_database_operation(operation: str, table: str, duration: float):
    """Log database operations"""
    logger = get_logger("db")
    logger.debug(f"DB Operation: {operation} on {table} - Duration: {duration:.3f}s")

def log_ml_operation(operation: str, details: dict):
    """Log ML operations"""
    logger = get_logger("ml")
    logger.info(f"ML Operation: {operation} - Details: {details}") 