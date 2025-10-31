"""
Configuration management
"""
import os
from pathlib import Path
from typing import Optional

from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """Application settings"""
    
    # API Server
    API_HOST: str = Field(default="0.0.0.0", env="API_HOST")
    API_PORT: int = Field(default=8000, env="API_PORT")
    API_WORKERS: int = Field(default=4, env="API_WORKERS")
    API_SECRET_KEY: str = Field(default="change-this-secret-key", env="API_SECRET_KEY")
    
    # Dashboard
    DASHBOARD_PORT: int = Field(default=7002, env="DASHBOARD_PORT")
    
    # Database
    DATABASE_URL: str = Field(
        default="sqlite:///./overwatch.db",
        env="DATABASE_URL"
    )
    
    # Logging
    LOG_LEVEL: str = Field(default="INFO", env="LOG_LEVEL")
    LOG_FILE: str = Field(default="./logs/overwatch.log", env="LOG_FILE")
    
    # Models
    MODEL_CACHE_DIR: str = Field(default="./models", env="MODEL_CACHE_DIR")
    ULTRALYTICS_MODEL_PATH: str = Field(
        default="./models/yolov8n.pt",
        env="ULTRALYTICS_MODEL_PATH"
    )
    DEVICE: str = Field(default="auto", env="DEVICE")  # auto, cuda, mps, or cpu
    
    # Storage
    SNAPSHOT_DIR: str = Field(default="./data/snapshots", env="SNAPSHOT_DIR")
    RECORDING_DIR: str = Field(default="./data/recordings", env="RECORDING_DIR")
    EVENT_DB_PATH: str = Field(default="./data/events.db", env="EVENT_DB_PATH")
    UPLOAD_DIR: str = Field(default="./data/uploads", env="UPLOAD_DIR")
    
    # Alerts
    WEBHOOK_URL: Optional[str] = Field(default=None, env="WEBHOOK_URL")
    SMTP_HOST: Optional[str] = Field(default=None, env="SMTP_HOST")
    SMTP_PORT: int = Field(default=587, env="SMTP_PORT")
    SMTP_USER: Optional[str] = Field(default=None, env="SMTP_USER")
    SMTP_PASSWORD: Optional[str] = Field(default=None, env="SMTP_PASSWORD")
    ALERT_EMAIL: Optional[str] = Field(default=None, env="ALERT_EMAIL")
    
    # Performance
    MAX_CONCURRENT_STREAMS: int = Field(default=16, env="MAX_CONCURRENT_STREAMS")
    FRAME_BUFFER_SIZE: int = Field(default=30, env="FRAME_BUFFER_SIZE")
    PROCESSING_THREADS: int = Field(default=4, env="PROCESSING_THREADS")
    
    # Security
    JWT_SECRET: str = Field(default="change-this-jwt-secret", env="JWT_SECRET")
    JWT_EXPIRY: int = Field(default=86400, env="JWT_EXPIRY")
    ENABLE_AUTH: bool = Field(default=False, env="ENABLE_AUTH")
    
    # Development
    DEBUG: bool = Field(default=False, env="DEBUG")
    AUTO_RELOAD: bool = Field(default=False, env="AUTO_RELOAD")
    
    # Federation
    NODE_ID: str = Field(default="overwatch-node-1", env="NODE_ID")
    NODE_TYPE: str = Field(default="central", env="NODE_TYPE")  # 'central' or 'edge'
    NODE_URL: str = Field(default="http://localhost:8000", env="NODE_URL")
    CENTRAL_SERVER_URL: Optional[str] = Field(default=None, env="CENTRAL_SERVER_URL")
    ENABLE_FEDERATION: bool = Field(default=False, env="ENABLE_FEDERATION")
    
    # ZeroTier / Overlay Network
    ENABLE_ZEROTIER: bool = Field(default=False, env="ENABLE_ZEROTIER")
    OVERLAY_PROVIDER: str = Field(default="zerotier", env="OVERLAY_PROVIDER")  # zerotier | none
    ZEROTIER_API_TOKEN: Optional[str] = Field(default=None, env="ZEROTIER_API_TOKEN")
    ZEROTIER_NETWORK_ID: Optional[str] = Field(default=None, env="ZEROTIER_NETWORK_ID")
    ZEROTIER_LOCAL_API_PORT: int = Field(default=9993, env="ZEROTIER_LOCAL_API_PORT")
    ZEROTIER_IP_RANGE_START: str = Field(default="10.147.0.1", env="ZEROTIER_IP_RANGE_START")
    ZEROTIER_IP_RANGE_END: str = Field(default="10.147.255.254", env="ZEROTIER_IP_RANGE_END")
    ZEROTIER_ROUTE_TARGET: str = Field(default="10.147.0.0/16", env="ZEROTIER_ROUTE_TARGET")
    ZEROTIER_NETWORK_NAME: str = Field(default="Overwatch Federation", env="ZEROTIER_NETWORK_NAME")
    
    # Paths
    CONFIG_DIR: str = Field(default="./config", env="CONFIG_DIR")
    CAMERAS_CONFIG: str = Field(
        default="./config/cameras.yaml",
        env="CAMERAS_CONFIG"
    )
    WORKFLOWS_CONFIG: str = Field(
        default="./config/workflows.yaml",
        env="WORKFLOWS_CONFIG"
    )
    
    class Config:
        env_file = ".env"
        case_sensitive = True


# Global settings instance
settings = Settings()

