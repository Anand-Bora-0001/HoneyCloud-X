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
    email_enabled: bool = False
    smtp_server: Optional[str] = None
    smtp_port: int = 587
    smtp_username: Optional[str] = None
    smtp_password: Optional[str] = None
    smtp_from_email: str = "alerts@honeycloud.com"
    smtp_from_name: str = "HoneyCloud Security"
    smtp_use_tls: bool = True
    alert_email_to: Optional[str] = None
    alert_email_from: Optional[str] = None
    resend_api_key: Optional[str] = None
    
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
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        import json
        
        # Parse SMTP_CONFIG if present in environment
        smtp_config_str = os.environ.get("SMTP_CONFIG")
        if smtp_config_str:
            try:
                smtp_config = json.loads(smtp_config_str)
                if isinstance(smtp_config, dict):
                    if "smtp_server" in smtp_config:
                        self.smtp_server = smtp_config["smtp_server"]
                    if "smtp_port" in smtp_config:
                        self.smtp_port = int(smtp_config["smtp_port"])
                    if "smtp_username" in smtp_config:
                        self.smtp_username = smtp_config["smtp_username"]
                    if "smtp_password" in smtp_config:
                        self.smtp_password = smtp_config["smtp_password"]
                    if "smtp_from_email" in smtp_config:
                        self.smtp_from_email = smtp_config["smtp_from_email"]
                    if "smtp_from_name" in smtp_config:
                        self.smtp_from_name = smtp_config["smtp_from_name"]
                    if "smtp_use_tls" in smtp_config:
                        val = smtp_config["smtp_use_tls"]
                        self.smtp_use_tls = val if isinstance(val, bool) else str(val).lower() in ("true", "1", "yes")
            except Exception as e:
                logging.getLogger("HoneyCloud").warning(f"Failed to parse SMTP_CONFIG JSON: {e}")

        # Parse TELEGRAM_CONFIG if present in environment
        telegram_config_str = os.environ.get("TELEGRAM_CONFIG")
        if telegram_config_str:
            try:
                telegram_config = json.loads(telegram_config_str)
                if isinstance(telegram_config, dict):
                    if "telegram_bot_token" in telegram_config:
                        self.telegram_bot_token = telegram_config["telegram_bot_token"]
                    if "telegram_chat_id" in telegram_config:
                        self.telegram_chat_id = telegram_config["telegram_chat_id"]
            except Exception as e:
                logging.getLogger("HoneyCloud").warning(f"Failed to parse TELEGRAM_CONFIG JSON: {e}")

        # Resolve base directory relative to backend if running from root
        from pathlib import Path
        base_dir = Path("backend") if Path("backend").is_dir() else Path(".")
        
        # Resolve reports_dir and logs_dir if they are relative paths
        reports_path = Path(self.reports_dir)
        if not reports_path.is_absolute():
            self.reports_dir = str((base_dir / reports_path).resolve())
            
        logs_path = Path(self.logs_dir)
        if not logs_path.is_absolute():
            self.logs_dir = str((base_dir / logs_path).resolve())
            
        # Resolve database_url if it's a relative sqlite database
        if (self.database_url.startswith("sqlite:///./") or self.database_url.startswith("sqlite:///")) and not self.database_url.endswith(":memory:"):
            db_rel = self.database_url.split("sqlite:///", 1)[1]
            if db_rel.startswith("./"):
                db_rel = db_rel[2:]
            db_path = (base_dir / db_rel).resolve()
            self.database_url = f"sqlite:///{db_path.as_posix()}"


    @property
    def is_telegram_configured(self) -> bool:
        """Check if Telegram is properly configured"""
        return bool(self.telegram_bot_token and self.telegram_chat_id)
    
    @property
    def is_email_configured(self) -> bool:
        """Check if email is properly configured"""
        return bool(self.email_enabled and self.smtp_server and self.smtp_username and self.smtp_password)
    
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