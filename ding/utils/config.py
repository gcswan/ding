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
from dataclasses import dataclass, field
from typing import List, Optional


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

    sms_enabled: bool = False
    twilio_account_sid: Optional[str] = None
    twilio_auth_token: Optional[str] = None
    twilio_from_number: Optional[str] = None
    sms_default_recipients: List[str] = field(default_factory=list)

    teams_enabled: bool = False
    teams_default_webhook: Optional[str] = None
    teams_timeout_seconds: float = 5.0

    # TODO: Add push notification service configuration
    # fcm_server_key: Optional[str] = None
    # apns_key_id: Optional[str] = None
    # apns_team_id: Optional[str] = None
    # apns_key_file: Optional[str] = None


@dataclass
class AppConfig:
    """Main application configuration."""

    environment: str = "development"
    debug: bool = True
    version: str = "0.1.0"

    server: ServerConfig = field(default_factory=ServerConfig)
    grpc: GrpcConfig = field(default_factory=GrpcConfig)
    database: DatabaseConfig = field(default_factory=DatabaseConfig)
    notifications: NotificationConfig = field(default_factory=NotificationConfig)

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
    config.debug = _get_env_bool("DING_DEBUG", config.debug)

    # Server configuration
    config.server.host = os.getenv("DING_HOST", config.server.host)
    config.server.port = int(os.getenv("DING_PORT", str(config.server.port)))
    config.server.log_level = os.getenv("DING_LOG_LEVEL", config.server.log_level)
    config.server.workers = int(os.getenv("DING_WORKERS", str(config.server.workers)))

    # gRPC configuration
    config.grpc.video_port = int(
        os.getenv("DING_GRPC_VIDEO_PORT", str(config.grpc.video_port))
    )
    config.grpc.doorbell_port = int(
        os.getenv("DING_GRPC_DOORBELL_PORT", str(config.grpc.doorbell_port))
    )
    config.grpc.max_workers = int(
        os.getenv("DING_GRPC_MAX_WORKERS", str(config.grpc.max_workers))
    )

    _load_notification_config(config)

    # TODO: Load database configuration
    # TODO: Load notification service configuration
    # TODO: Validate configuration values

    return config


def _get_env_bool(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _parse_recipients(raw: Optional[str]) -> List[str]:
    if not raw:
        return []
    return [item.strip() for item in raw.split(",") if item.strip()]


def _load_notification_config(config: AppConfig) -> None:
    notifications = config.notifications

    notifications.sms_enabled = _get_env_bool(
        "DING_SMS_ENABLED", notifications.sms_enabled
    )
    notifications.twilio_account_sid = os.getenv(
        "DING_TWILIO_ACCOUNT_SID", notifications.twilio_account_sid
    )
    notifications.twilio_auth_token = os.getenv(
        "DING_TWILIO_AUTH_TOKEN", notifications.twilio_auth_token
    )
    notifications.twilio_from_number = os.getenv(
        "DING_TWILIO_FROM_NUMBER", notifications.twilio_from_number
    )
    notifications.sms_default_recipients = _parse_recipients(
        os.getenv("DING_SMS_RECIPIENTS")
    ) or notifications.sms_default_recipients

    notifications.teams_enabled = _get_env_bool(
        "DING_TEAMS_ENABLED", notifications.teams_enabled
    )
    notifications.teams_default_webhook = os.getenv(
        "DING_TEAMS_WEBHOOK", notifications.teams_default_webhook
    )
    timeout_raw = os.getenv("DING_TEAMS_TIMEOUT")
    if timeout_raw:
        try:
            notifications.teams_timeout_seconds = float(timeout_raw)
        except ValueError:
            pass


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
