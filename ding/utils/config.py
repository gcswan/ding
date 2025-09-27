"""
Configuration management for the Ding doorbell application.

This module handles loading and validating configuration from various sources:
- Environment variables
- Configuration files
- Command-line arguments
- Default values

TODO: Add configuration validation with Pydantic
TODO: Implement configuration hot-reloading
TODO: Add configuration encryption for sensitive values
TODO: Support multiple configuration formats (YAML, TOML, JSON)
"""

import os
from typing import Optional, Dict, Any
from dataclasses import dataclass


@dataclass
class ServerConfig:
    """Server configuration settings."""
    host: str = "0.0.0.0"
    port: int = 8000
    reload: bool = False
    workers: int = 1
    log_level: str = "info"

    # TODO: Add SSL/TLS configuration
    # ssl_keyfile: Optional[str] = None
    # ssl_certfile: Optional[str] = None


@dataclass
class GrpcConfig:
    """gRPC services configuration."""
    video_port: int = 50051
    doorbell_port: int = 50052
    max_workers: int = 10

    # TODO: Add gRPC-specific settings
    # max_message_size: int = 4 * 1024 * 1024  # 4MB
    # compression: str = "gzip"
    # keepalive_time: int = 30


@dataclass
class DatabaseConfig:
    """Database configuration (for future implementation)."""
    # TODO: Add database configuration when implemented
    # url: Optional[str] = None
    # pool_size: int = 10
    # max_overflow: int = 20
    pass


@dataclass
class NotificationConfig:
    """Notification service configuration."""
    # TODO: Add push notification service configuration
    # fcm_server_key: Optional[str] = None
    # apns_key_id: Optional[str] = None
    # apns_team_id: Optional[str] = None
    # apns_key_file: Optional[str] = None
    pass


@dataclass
class AppConfig:
    """Main application configuration."""
    environment: str = "development"
    debug: bool = True
    version: str = "0.1.0"

    server: ServerConfig = ServerConfig()
    grpc: GrpcConfig = GrpcConfig()
    database: DatabaseConfig = DatabaseConfig()
    notifications: NotificationConfig = NotificationConfig()

    # TODO: Add feature flags
    # enable_analytics: bool = True
    # enable_recording: bool = False
    # max_session_duration: int = 300  # 5 minutes


def load_config() -> AppConfig:
    """
    Load configuration from environment variables and defaults.

    TODO: Add configuration file loading
    TODO: Implement configuration validation
    TODO: Add configuration merging from multiple sources
    """
    config = AppConfig()

    # Load environment-specific overrides
    config.environment = os.getenv("DING_ENVIRONMENT", config.environment)
    config.debug = os.getenv("DING_DEBUG", "true").lower() == "true"

    # Server configuration
    config.server.host = os.getenv("DING_HOST", config.server.host)
    config.server.port = int(os.getenv("DING_PORT", str(config.server.port)))
    config.server.log_level = os.getenv("DING_LOG_LEVEL", config.server.log_level)
    config.server.workers = int(os.getenv("DING_WORKERS", str(config.server.workers)))

    # gRPC configuration
    config.grpc.video_port = int(os.getenv("DING_GRPC_VIDEO_PORT", str(config.grpc.video_port)))
    config.grpc.doorbell_port = int(os.getenv("DING_GRPC_DOORBELL_PORT", str(config.grpc.doorbell_port)))
    config.grpc.max_workers = int(os.getenv("DING_GRPC_MAX_WORKERS", str(config.grpc.max_workers)))

    # TODO: Load database configuration
    # TODO: Load notification service configuration
    # TODO: Validate configuration values

    return config


def get_config() -> AppConfig:
    """
    Get the current application configuration.

    This function implements a singleton pattern to ensure configuration
    is loaded only once and reused throughout the application.

    TODO: Add configuration caching
    TODO: Implement configuration refresh mechanism
    """
    if not hasattr(get_config, "_config"):
        get_config._config = load_config()

    return get_config._config