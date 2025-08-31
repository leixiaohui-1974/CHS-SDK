from pydantic_settings import BaseSettings
from typing import List, Optional
import os
from pathlib import Path

class Settings(BaseSettings):
    """
    Application settings using Pydantic BaseSettings
    """
    
    # Application settings
    app_name: str = "CHS-SDK API"
    app_version: str = "1.0.0"
    app_description: str = "API for the China Hydraulic Simulation SDK"
    debug: bool = False
    
    # Server settings
    host: str = "0.0.0.0"
    port: int = 8000
    reload: bool = False
    
    # CORS settings
    cors_origins: List[str] = ["*"]
    cors_credentials: bool = True
    cors_methods: List[str] = ["*"]
    cors_headers: List[str] = ["*"]
    
    # Database settings
    database_url: str = "sqlite:///./simulation.db"
    database_echo: bool = False
    
    # Redis settings
    redis_url: str = "redis://localhost:6379/0"
    redis_password: Optional[str] = None
    
    # WebSocket settings
    websocket_heartbeat_interval: int = 30  # seconds
    websocket_timeout: int = 60  # seconds
    websocket_max_connections: int = 100
    
    # Simulation settings
    max_simulation_sessions: int = 10
    simulation_timeout: int = 3600  # seconds
    default_time_step: float = 1.0  # seconds
    max_simulation_steps: int = 100000
    
    # File storage settings
    upload_dir: str = "uploads"
    max_file_size: int = 100 * 1024 * 1024  # 100MB
    allowed_file_types: List[str] = [".json", ".yaml", ".yml", ".csv"]
    
    # Logging settings
    log_level: str = "INFO"
    log_format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    log_file: Optional[str] = None
    
    # Security settings
    secret_key: str = "your-secret-key-change-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    
    # API settings
    api_prefix: str = "/api"
    docs_url: str = "/docs"
    redoc_url: str = "/redoc"
    openapi_url: str = "/openapi.json"
    
    # Performance settings
    worker_processes: int = 1
    max_requests: int = 1000
    max_requests_jitter: int = 100
    
    # Monitoring settings
    enable_metrics: bool = True
    metrics_port: int = 9090
    
    # Examples directory
    examples_dir: str = "examples"
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
        
    def get_database_url(self) -> str:
        """
        Get the database URL with proper formatting
        """
        if self.database_url.startswith("sqlite"):
            # Ensure the directory exists for SQLite
            db_path = self.database_url.replace("sqlite:///", "")
            db_dir = Path(db_path).parent
            db_dir.mkdir(parents=True, exist_ok=True)
        return self.database_url
    
    def get_upload_dir(self) -> Path:
        """
        Get the upload directory as a Path object
        """
        upload_path = Path(self.upload_dir)
        upload_path.mkdir(parents=True, exist_ok=True)
        return upload_path
    
    def get_examples_dir(self) -> Optional[Path]:
        """
        Get the examples directory if it exists
        """
        current_dir = Path(__file__).parent
        
        # Check common locations
        possible_paths = [
            current_dir / self.examples_dir,
            current_dir.parent / self.examples_dir,
            current_dir.parent.parent / self.examples_dir,
            Path.cwd() / self.examples_dir
        ]
        
        for path in possible_paths:
            if path.exists() and path.is_dir():
                return path
        
        return None
    
    def is_development(self) -> bool:
        """
        Check if running in development mode
        """
        return self.debug or self.reload
    
    def is_production(self) -> bool:
        """
        Check if running in production mode
        """
        return not self.is_development()

# Global settings instance
settings = Settings()

# Environment-specific configurations
class DevelopmentSettings(Settings):
    debug: bool = True
    reload: bool = True
    log_level: str = "DEBUG"
    database_echo: bool = True
    cors_origins: List[str] = ["http://localhost:3000", "http://127.0.0.1:3000"]

class ProductionSettings(Settings):
    debug: bool = False
    reload: bool = False
    log_level: str = "WARNING"
    database_echo: bool = False
    cors_origins: List[str] = []  # Should be set via environment variables
    secret_key: str = os.getenv("SECRET_KEY", "change-me-in-production")

class TestingSettings(Settings):
    debug: bool = True
    database_url: str = "sqlite:///./test.db"
    redis_url: str = "redis://localhost:6379/1"
    max_simulation_sessions: int = 5
    websocket_max_connections: int = 10

def get_settings() -> Settings:
    """
    Get settings based on environment
    """
    env = os.getenv("ENVIRONMENT", "development").lower()
    
    if env == "production":
        return ProductionSettings()
    elif env == "testing":
        return TestingSettings()
    else:
        return DevelopmentSettings()

# Export the appropriate settings
settings = get_settings()