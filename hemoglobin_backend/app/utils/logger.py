"""
Structured logging with PHI anonymization.
"""
import logging
import sys
from pythonjsonlogger import jsonlogger
from app.config import settings


class PHISafeFormatter(jsonlogger.JsonFormatter):
    """Custom JSON formatter that filters out PHI."""
    
    SENSITIVE_FIELDS = {'user_id', 'patient_id', 'name', 'email', 'phone', 'dob'}
    
    def process_log_record(self, log_record):
        """Remove or mask sensitive fields."""
        for field in self.SENSITIVE_FIELDS:
            if field in log_record:
                log_record[field] = "***REDACTED***"
        return super().process_log_record(log_record)


def setup_logger(name: str) -> logging.Logger:
    """
    Create a logger with PHI-safe formatting.
    
    Args:
        name: Logger name (typically __name__)
        
    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, settings.log_level.upper()))
    
    # Console handler with JSON formatting
    handler = logging.StreamHandler(sys.stdout)
    formatter = PHISafeFormatter(
        '%(timestamp)s %(level)s %(name)s %(message)s',
        rename_fields={'timestamp': '@timestamp', 'level': 'severity'}
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    
    return logger


# Create default logger
logger = setup_logger(__name__)
