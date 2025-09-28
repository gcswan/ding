"""
Pydantic models for the Ding doorbell application.

These models define the data structures used in the REST API endpoints.
They provide validation, serialization, and documentation for the API.

TODO: Add comprehensive field validation
TODO: Implement proper error handling models
TODO: Add support for API versioning
TODO: Create models for user management and authentication
"""

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field
from enum import Enum


class ResponseType(str, Enum):
    """Door owner response types to ding requests."""
    ACCEPT = "accept"
    REJECT = "reject"
    BUSY = "busy"
    CUSTOM = "custom"


class NotificationType(str, Enum):
    """Types of notifications sent to door owners."""
    DING_REQUEST = "ding_request"
    DING_TIMEOUT = "ding_timeout"
    DING_ACCEPTED = "ding_accepted"
    DING_REJECTED = "ding_rejected"


class QRCodeScanRequest(BaseModel):
    """Request model for QR code scanning."""
    qr_code_id: str = Field(..., description="Unique QR code identifier")
    scanner_device_id: str = Field(..., description="Device ID of the scanning device")
    scanner_location: Optional[str] = Field(None, description="Optional location data")
    timestamp: Optional[datetime] = Field(default_factory=datetime.now, description="Scan timestamp")

    # TODO: Add scanner profile information
    # scanner_name: Optional[str] = None
    # scanner_phone: Optional[str] = None
    # scanner_photo: Optional[str] = None  # Base64 encoded or URL


class QRCodeScanResponse(BaseModel):
    """Response model for QR code scanning."""
    success: bool = Field(..., description="Whether the scan was successful")
    message: str = Field(..., description="Response message")
    session_id: Optional[str] = Field(None, description="Session ID for potential video chat")
    door_owner_id: Optional[str] = Field(None, description="ID of the door owner")
    estimated_response_time: Optional[int] = Field(None, description="Estimated response time in seconds")

    # TODO: Add door owner's custom greeting message
    # greeting_message: Optional[str] = None
    # custom_instructions: Optional[str] = None


class DingResponse(BaseModel):
    """Door owner's response to a ding request."""
    session_id: str = Field(..., description="Session ID of the ding request")
    door_owner_id: str = Field(..., description="ID of the responding door owner")
    response_type: ResponseType = Field(..., description="Type of response")
    custom_message: Optional[str] = Field(None, description="Optional custom response message")

    # TODO: Add response templates and quick replies
    # template_id: Optional[str] = None
    # scheduled_response: Optional[datetime] = None


class DingResponseResult(BaseModel):
    """Result of door owner's response to a ding."""
    success: bool = Field(..., description="Whether the response was processed successfully")
    message: str = Field(..., description="Result message")
    video_session_id: Optional[str] = Field(None, description="Video session ID if accepted")

    # TODO: Add connection details for video session
    # video_server_host: Optional[str] = None
    # video_server_port: Optional[int] = None
    # session_token: Optional[str] = None


class NotificationModel(BaseModel):
    """Notification sent to door owners."""
    notification_id: str = Field(..., description="Unique notification identifier")
    door_owner_id: str = Field(..., description="ID of the door owner")
    scanner_device_id: str = Field(..., description="ID of the scanning device")
    notification_type: NotificationType = Field(..., description="Type of notification")
    message: str = Field(..., description="Notification message")
    timestamp: datetime = Field(..., description="Notification timestamp")
    session_id: Optional[str] = Field(None, description="Associated session ID")

    # TODO: Add rich notification content
    # image_url: Optional[str] = None
    # sound_url: Optional[str] = None
    # priority: Optional[int] = None


class QRCodeGenerationRequest(BaseModel):
    """Request to generate a new QR code for a door owner."""
    door_owner_id: str = Field(..., description="ID of the door owner")
    label: Optional[str] = Field(None, description="Optional label for the QR code")
    expiry_date: Optional[datetime] = Field(None, description="Optional expiry date")
    sms_recipients: Optional[List[str]] = Field(
        None,
        description="Phone numbers that should receive SMS alerts for this QR code",
    )
    teams_webhook_url: Optional[str] = Field(
        None,
        description="Microsoft Teams webhook URL for ding notifications",
    )

    # TODO: Add QR code customization options
    # logo_url: Optional[str] = None
    # color_scheme: Optional[str] = None
    # size: Optional[str] = None


class QRCodeGenerationResponse(BaseModel):
    """Response containing generated QR code information."""
    qr_code_id: str = Field(..., description="Unique QR code identifier")
    qr_code_url: str = Field(..., description="URL to the QR code image")
    qr_code_data: str = Field(..., description="QR code data string")
    created_at: datetime = Field(..., description="Creation timestamp")
    expires_at: Optional[datetime] = Field(None, description="Expiry timestamp")

    # TODO: Add usage analytics
    # scan_count: int = 0
    # last_scanned: Optional[datetime] = None


class VideoSessionInfo(BaseModel):
    """Information about a video chat session."""
    session_id: str = Field(..., description="Unique session identifier")
    door_owner_id: str = Field(..., description="ID of the door owner")
    visitor_device_id: str = Field(..., description="ID of the visitor device")
    status: str = Field(..., description="Current session status")
    created_at: datetime = Field(..., description="Session creation time")
    started_at: Optional[datetime] = Field(None, description="Session start time")
    ended_at: Optional[datetime] = Field(None, description="Session end time")

    # TODO: Add session quality metrics
    # duration_seconds: Optional[int] = None
    # video_quality: Optional[str] = None
    # connection_quality: Optional[str] = None


class ErrorResponse(BaseModel):
    """Standard error response model."""
    error: bool = True
    error_code: str = Field(..., description="Error code identifier")
    message: str = Field(..., description="Human-readable error message")
    details: Optional[dict] = Field(None, description="Additional error details")
    timestamp: datetime = Field(default_factory=datetime.now, description="Error timestamp")

    # TODO: Add request tracing information
    # trace_id: Optional[str] = None
    # request_id: Optional[str] = None


class HealthCheck(BaseModel):
    """Health check response model."""
    status: str = Field(..., description="Service status")
    timestamp: datetime = Field(default_factory=datetime.now, description="Check timestamp")
    version: str = Field(..., description="Application version")
    uptime_seconds: int = Field(..., description="Server uptime in seconds")

    # TODO: Add detailed health metrics
    # grpc_server_status: str = "unknown"
    # database_status: str = "unknown"
    # notification_service_status: str = "unknown"
