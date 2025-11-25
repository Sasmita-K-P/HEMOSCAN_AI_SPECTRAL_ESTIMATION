"""
Configuration management for the Hemoglobin Estimation API.
Uses Pydantic Settings for environment variable management.
"""
from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path
from typing import Optional


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Application
    app_name: str = "Hemoglobin Estimation API"
    app_version: str = "1.0.0"
    debug: bool = True
    log_level: str = "INFO"
    
    # Server
    host: str = "0.0.0.0"
    port: int = 8000
    
    # File Storage
    upload_dir: Path = Path("./data/uploads")
    processed_dir: Path = Path("./data/processed")
    model_dir: Path = Path("./data/models")
    max_upload_size_mb: int = 8
    
    # Model Paths
    unet_model_path: Path = Path("./data/models/unet_v1.0.0.h5")
    hb_model_path: Path = Path("./data/models/hb_predictor_v1.0.0.h5")
    
    # Quality Control Thresholds
    qc_min_sharpness: float = 30.0
    qc_min_brightness: float = 50.0
    qc_max_brightness: float = 220.0
    qc_min_contrast: float = 15.0
    qc_max_glare_coverage: float = 0.15
    
    # Preprocessing
    target_size: int = 512
    roi_size: int = 256
    random_seed: int = 42
    
    # Prediction
    mc_dropout_passes: int = 10
    uncertainty_threshold: float = 0.7
    confidence_level: float = 0.95
    
    # Anemia Thresholds (WHO guidelines, g/dL)
    anemia_threshold_normal: float = 12.0
    anemia_threshold_mild: float = 11.0
    anemia_threshold_moderate: float = 8.0
    
    # Database
    database_url: str = "sqlite:///./data/hemoglobin.db"
    
    # Security
    encryption_key: str = "your-secret-key-here-change-in-production"
    enable_encryption: bool = False
    
    # Monitoring
    enable_metrics: bool = True
    metrics_port: int = 9090
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False
    )
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Create directories if they don't exist
        self.upload_dir.mkdir(parents=True, exist_ok=True)
        self.processed_dir.mkdir(parents=True, exist_ok=True)
        self.model_dir.mkdir(parents=True, exist_ok=True)


# Global settings instance
settings = Settings()
