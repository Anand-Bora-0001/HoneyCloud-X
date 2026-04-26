"""
HoneyCloud Configuration Management
Handles environment variables and application settings
"""
import os
from typing import Optional
from pydantic_settings import BaseSettings
from pydantic import validator
import logging

class Settings(BaseSettings):
    """Application settings with environment variable support"""
    
    # Application
    app_name: str = "HoneyCloud"
    app_version: str = "2.0.0"
    debug: bool = False
    log_level: str = "INFO"
    timezone: str = "UTC"
    
    # Server
    host: str = "0.0.0.0"
    port: int = 8000
    reload: bool = False
    
    # Database
    database_url: str = "sqlite:///./honeycloud.db"
    
    # Security
    jwt_secret_key: str = "your-super-secret-jwt-key-change-this-in-production"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 60
    
    # Telegram
    telegram_bot_token: Optional[str] = None
    telegram_chat_id: Optional[str] = None
    
    # Email/SMTP
    smtp_server: Optional[str] = None
    smtp_port: int = 587
    smtp_username: Optional[str] = None
    smtp_password: Optional[str] = None
    smtp_from_email: str = "alerts@honeycloud.com"
    smtp_from_name: str = "HoneyCloud Security"
    smtp_use_tls: bool = True
    
    # Rate Limiting
    rate_limit_per_minute: int = 100
    max_events_per_hour: int = 1000
    
    # Alerts
    alert_cooldown_minutes: int = 5
    max_alerts_per_hour: int = 20
    
    # File Storage
    reports_dir: str = "reports"
    logs_dir: str = "logs"
    upload_max_size: int = 10485760  # 10MB
    
    # External APIs
    ipapi_key: Optional[str] = None
    abuseipdb_key: Optional[str] = None
    
    @validator('log_level')
    def validate_log_level(cls, v):
        valid_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
        if v.upper() not in valid_levels:
            raise ValueError(f'Log level must be one of: {valid_levels}')
        return v.upper()
    
    @validator('jwt_secret_key')
    def validate_jwt_secret(cls, v):
        if len(v) < 32:
            raise ValueError('JWT secret key must be at least 32 characters long')
        return v
    
    @property
    def is_telegram_configured(self) -> bool:
        """Check if Telegram is properly configured"""
        return bool(self.telegram_bot_token and self.telegram_chat_id)
    
    @property
    def is_email_configured(self) -> bool:
        """Check if email is properly configured"""
        return bool(self.smtp_server and self.smtp_username and self.smtp_password)
    
    def setup_directories(self):
        """Create necessary directories"""
        os.makedirs(self.reports_dir, exist_ok=True)
        os.makedirs(self.logs_dir, exist_ok=True)
    
    def setup_logging(self):
        """Configure application logging"""
        log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        
        # Fix Windows console encoding for emoji/Unicode characters
        import sys
        import io
        
        # Force UTF-8 on Windows stdout/stderr so all handlers work
        if sys.platform == 'win32':
            os.environ['PYTHONIOENCODING'] = 'utf-8'
            try:
                sys.stdout.reconfigure(encoding='utf-8', errors='replace')
                sys.stderr.reconfigure(encoding='utf-8', errors='replace')
            except Exception:
                # Fallback: wrap the buffer streams
                sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
                sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
        
        console_handler = logging.StreamHandler(stream=sys.stdout)
        console_handler.setFormatter(logging.Formatter(log_format))
        
        # File handler with rotation (UTF-8 encoding for log files)
        from logging.handlers import RotatingFileHandler
        file_handler = RotatingFileHandler(
            f"{self.logs_dir}/honeycloud.log",
            maxBytes=10485760,  # 10MB
            backupCount=5,
            encoding='utf-8'
        )
        file_handler.setFormatter(logging.Formatter(log_format))
        
        # Configure root logger
        logging.basicConfig(
            level=getattr(logging, self.log_level),
            handlers=[console_handler, file_handler],
            format=log_format
        )
        
        # Reduce noise from external libraries
        logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
        logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
        extra = "ignore"

# Global settings instance
settings = Settings()

# Setup on import
settings.setup_directories()
settings.setup_logging()

# Export commonly used values
DATABASE_URL = settings.database_url
JWT_SECRET_KEY = settings.jwt_secret_key
JWT_ALGORITHM = settings.jwt_algorithm
ACCESS_TOKEN_EXPIRE_MINUTES = settings.jwt_expire_minutes