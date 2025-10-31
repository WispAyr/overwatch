"""
Logging configuration
"""
import logging
import sys
import re
from pathlib import Path
from logging.handlers import RotatingFileHandler

from .config import settings


# Sensitive keys to redact from logs
SENSITIVE_KEYS = [
    'ZEROTIER_API_TOKEN',
    'Authorization',
    'Bearer',
    'JWT_SECRET',
    'API_SECRET_KEY',
    'SMTP_PASSWORD',
    'password',
    'token',
    'secret',
    'api_key'
]


class SecretRedactingFormatter(logging.Formatter):
    """Formatter that redacts sensitive information from log messages"""
    
    def format(self, record):
        # Format the message first
        original_message = super().format(record)
        
        # Redact sensitive values
        redacted_message = original_message
        
        # Redact Authorization headers
        redacted_message = re.sub(
            r'(Authorization|Bearer|X-ZT1-Auth):\s*[A-Za-z0-9+/=_-]+',
            r'\1: [REDACTED]',
            redacted_message,
            flags=re.IGNORECASE
        )
        
        # Redact API tokens in URLs
        redacted_message = re.sub(
            r'(token|api_token|auth)=[A-Za-z0-9+/=_-]+',
            r'\1=[REDACTED]',
            redacted_message,
            flags=re.IGNORECASE
        )
        
        # Redact known sensitive keys
        for key in SENSITIVE_KEYS:
            redacted_message = re.sub(
                f'{key}["\']?\\s*[:=]\\s*["\']?([^"\'\\s,}}]+)',
                f'{key}: [REDACTED]',
                redacted_message,
                flags=re.IGNORECASE
            )
        
        return redacted_message


def setup_logging() -> logging.Logger:
    """Setup application logging"""
    
    # Create logs directory
    log_file = Path(settings.LOG_FILE)
    log_file.parent.mkdir(parents=True, exist_ok=True)
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, settings.LOG_LEVEL.upper()))
    
    # Clear existing handlers
    root_logger.handlers.clear()
    
    # Console handler with secret redaction
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(getattr(logging, settings.LOG_LEVEL.upper()))
    console_formatter = SecretRedactingFormatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    console_handler.setFormatter(console_formatter)
    root_logger.addHandler(console_handler)
    
    # File handler with secret redaction
    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=10_000_000,  # 10MB
        backupCount=5
    )
    file_handler.setLevel(logging.DEBUG)
    file_formatter = SecretRedactingFormatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    file_handler.setFormatter(file_formatter)
    root_logger.addHandler(file_handler)
    
    # Get overwatch logger
    logger = logging.getLogger('overwatch')
    
    return logger

