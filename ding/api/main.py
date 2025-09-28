"""
FastAPI REST API for the Ding Doorbell Application

This module provides HTTP REST endpoints that complement the gRPC services.
It's designed to be mobile-friendly and provides easy integration for web clients.

ARCHITECTURE OVERVIEW:
- REST API for mobile clients and web interfaces
- Bridges between HTTP clients and gRPC services
- Handles QR code generation and management
- Provides WebSocket endpoints for real-time notifications
- TODO: Add authentication and authorization middleware
- TODO: Implement rate limiting and request validation
- TODO: Add comprehensive API documentation
"""

import asyncio
import base64
import io
import logging
import uuid
from datetime import datetime

import qrcode
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

# Import our models
from ..models.schemas import (
    QRCodeScanRequest,
    QRCodeScanResponse,
    DingResponse,
    DingResponseResult,
    QRCodeGenerationRequest,
    QRCodeGenerationResponse,
    VideoSessionInfo,
    HealthCheck,
)
from ..utils.config import get_config
from ..utils.notifications import NotificationManager
from ..utils.store import OwnerContact, store

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Ding Doorbell API",
    description="REST API for the Ding doorbell application with QR code scanning and video chat",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

config = get_config()
notification_manager = NotificationManager(config.notifications)

# Configure CORS - TODO: Restrict to specific domains in production
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # TODO: Configure specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/", response_model=dict)
async def root():
    """Root endpoint with basic API information."""
    return {
        "service": "Ding Doorbell API",
        "version": "0.1.0",
        "description": "REST API for doorbell functionality with QR codes and video chat",
        "docs": "/docs",
        "health": "/health"
    }


@app.get("/health", response_model=HealthCheck)
async def health_check():
    """Health check endpoint for monitoring and load balancers."""
    uptime = int((datetime.now() - store.start_time).total_seconds())

    # TODO: Add checks for dependent services
    # - gRPC server status
    # - Database connectivity
    # - External service availability

    return HealthCheck(
        status="healthy",
        version="0.1.0",
        uptime_seconds=uptime
    )


@app.post("/scan", response_model=QRCodeScanResponse)
async def scan_qr_code(request: QRCodeScanRequest):
    """
    Handle QR code scanning from mobile devices.

    This endpoint:
    1. Validates the QR code
    2. Creates a new ding session
    3. Sends notification to door owner (via gRPC or WebSocket)
    4. Returns session information to the scanner

    TODO: Add rate limiting per device
    TODO: Implement geolocation validation
    TODO: Add abuse detection and prevention
    """
    logger.info(
        "QR code scan request: %s from %s",
        request.qr_code_id,
        request.scanner_device_id,
    )

    qr_data = await store.get_qr_code(request.qr_code_id)
    if not qr_data:
        raise HTTPException(
            status_code=404,
            detail="QR code not found or expired"
        )

    door_owner_id = qr_data["door_owner_id"]

    session_id = f"session_{uuid.uuid4().hex}"
    created_at = datetime.now()

    session_data = {
        "session_id": session_id,
        "door_owner_id": door_owner_id,
        "scanner_device_id": request.scanner_device_id,
        "qr_code_id": request.qr_code_id,
        "created_at": created_at,
        "status": "pending",
        "scanner_location": request.scanner_location,
    }

    await store.add_session(session_id, session_data)

    await _notify_door_owner(door_owner_id, session_data)

    return QRCodeScanResponse(
        success=True,
        message="QR code scanned successfully. Door owner has been notified.",
        session_id=session_id,
        door_owner_id=door_owner_id,
        estimated_response_time=30  # TODO: Make this configurable
    )


@app.post("/respond", response_model=DingResponseResult)
async def respond_to_ding(response: DingResponse):
    """
    Handle door owner's response to a ding request.

    When a door owner responds:
    1. Validate the session
    2. Update session status
    3. If accepted, initiate video chat session
    4. Notify the scanner about the response

    TODO: Add authentication for door owners
    TODO: Implement response templates
    TODO: Add automatic response scheduling
    """
    logger.info(f"Ding response: {response.response_type} for session {response.session_id}")

    session_data = await store.get_session(response.session_id)
    if not session_data:
        raise HTTPException(
            status_code=404,
            detail="Session not found or expired"
        )

    if session_data["door_owner_id"] != response.door_owner_id:
        raise HTTPException(
            status_code=403,
            detail="Unauthorized to respond to this session"
        )

    now = datetime.now()
    await store.update_session(
        response.session_id,
        {
            "status": "responded",
            "response_type": response.response_type.value,
            "response_message": response.custom_message,
            "responded_at": now,
        },
    )

    if response.response_type.value == "accept":
        # Create video session
        video_session_id = f"video_{response.session_id}"
        await store.update_session(
            response.session_id,
            {
                "video_session_id": video_session_id,
                "status": "video_chat_starting",
            },
        )

        # TODO: Initialize video chat session with gRPC video service
        # TODO: Send connection details to both clients

        message = "Ding accepted. Video chat session starting."

        logger.info(f"Video session {video_session_id} created for {response.session_id}")

        return DingResponseResult(
            success=True,
            message=message,
            video_session_id=video_session_id
        )

    else:
        await store.update_session(
            response.session_id,
            {"status": "declined", "closed_at": now},
        )

        response_messages = {
            "reject": "Door owner declined the request",
            "busy": "Door owner is busy, please try later",
            "custom": response.custom_message or "Custom response",
        }

        message = response_messages.get(response.response_type.value, "Unknown response")

        return DingResponseResult(
            success=True,
            message=message,
            video_session_id=None
        )


@app.post("/qr-codes", response_model=QRCodeGenerationResponse)
async def generate_qr_code(request: QRCodeGenerationRequest):
    """
    Generate a new QR code for a door owner.

    This endpoint creates a unique QR code that can be printed and placed
    at a door or entrance. When scanned, it will trigger the doorbell flow.

    TODO: Add authentication for door owners
    TODO: Implement QR code expiry and rotation
    TODO: Add usage analytics and tracking
    """
    logger.info("QR code generation request for door owner: %s", request.door_owner_id)

    qr_code_id = f"qr_{uuid.uuid4().hex}"

    # Create QR code data - this would be the URL that mobile apps scan
    # TODO: Configure base URL from environment
    qr_data = f"https://ding.app/scan/{qr_code_id}"

    # Generate QR code image
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(qr_data)
    qr.make(fit=True)

    # Create QR code image
    img = qr.make_image(fill_color="black", back_color="white")

    # Convert to base64 for API response
    buffer = io.BytesIO()
    img.save(buffer, format='PNG')
    img_str = base64.b64encode(buffer.getvalue()).decode()
    qr_code_url = f"data:image/png;base64,{img_str}"

    # Store QR code metadata
    qr_metadata = {
        "qr_code_id": qr_code_id,
        "door_owner_id": request.door_owner_id,
        "label": request.label,
        "created_at": datetime.now(),
        "expires_at": request.expiry_date,
        "scan_count": 0,
        "last_scanned": None,
    }

    await store.add_qr_code(qr_code_id, qr_metadata)

    existing_contact = await store.get_owner_contact(request.door_owner_id)
    sms_recipients = (
        request.sms_recipients
        if request.sms_recipients is not None
        else (existing_contact.sms_recipients if existing_contact else [])
    )
    teams_webhook = (
        request.teams_webhook_url
        if request.teams_webhook_url is not None
        else (existing_contact.teams_webhook_url if existing_contact else None)
    )

    metadata = dict(existing_contact.metadata) if existing_contact else {}
    metadata.update({"last_qr_code_id": qr_code_id, "label": request.label})

    contact = OwnerContact(
        door_owner_id=request.door_owner_id,
        sms_recipients=list(sms_recipients or []),
        teams_webhook_url=teams_webhook,
        metadata=metadata,
    )
    await store.set_owner_contact(contact)

    return QRCodeGenerationResponse(
        qr_code_id=qr_code_id,
        qr_code_url=qr_code_url,
        qr_code_data=qr_data,
        created_at=qr_metadata["created_at"],
        expires_at=qr_metadata["expires_at"]
    )


@app.get("/sessions/{session_id}", response_model=VideoSessionInfo)
async def get_session_info(session_id: str):
    """
    Get information about a specific session.

    TODO: Add authentication to restrict access
    TODO: Add session history and analytics
    """
    session_data = await store.get_session(session_id)
    if not session_data:
        raise HTTPException(status_code=404, detail="Session not found")

    return VideoSessionInfo(
        session_id=session_data["session_id"],
        door_owner_id=session_data["door_owner_id"],
        visitor_device_id=session_data["scanner_device_id"],
        status=session_data["status"],
        created_at=session_data["created_at"],
        started_at=session_data.get("started_at"),
        ended_at=session_data.get("ended_at")
    )


@app.websocket("/ws/notifications/{door_owner_id}")
async def websocket_notifications(websocket: WebSocket, door_owner_id: str):
    """
    WebSocket endpoint for real-time notifications to door owners.

    This provides an alternative to gRPC streaming for web clients
    and mobile apps that prefer WebSocket connections.

    TODO: Add authentication and authorization
    TODO: Implement proper error handling and reconnection
    TODO: Add message queuing for offline clients
    """
    await websocket.accept()
    await store.add_websocket(door_owner_id, websocket)

    logger.info("WebSocket connection established for door owner: %s", door_owner_id)

    try:
        while True:
            # Keep connection alive and handle incoming messages
            # TODO: Implement heartbeat mechanism
            await asyncio.sleep(30)

            # Send heartbeat
            await websocket.send_json({
                "type": "heartbeat",
                "timestamp": datetime.now().isoformat()
            })

    except WebSocketDisconnect:
        logger.info("WebSocket disconnected for door owner: %s", door_owner_id)
    except Exception as e:
        logger.error("WebSocket error for %s: %s", door_owner_id, e)
    finally:
        await store.pop_websocket(door_owner_id)


async def _notify_door_owner(door_owner_id: str, session_data: dict):
    """Send WebSocket plus out-of-band notifications for a new ding."""
    notification = {
        "type": "ding_request",
        "session_id": session_data["session_id"],
        "scanner_device_id": session_data["scanner_device_id"],
        "message": "Someone is at your door and wants to talk!",
        "timestamp": datetime.now().isoformat(),
        "scanner_location": session_data.get("scanner_location"),
    }

    websocket = await store.get_websocket(door_owner_id)
    if websocket:
        try:
            await websocket.send_json(notification)
            logger.info("WebSocket notification sent to %s", door_owner_id)
        except Exception as exc:
            logger.error("Failed to send WebSocket notification to %s: %s", door_owner_id, exc)
            await store.pop_websocket(door_owner_id)

    contact = await store.get_owner_contact(door_owner_id)
    if not contact:
        contact = OwnerContact(door_owner_id=door_owner_id)

    asyncio.create_task(_dispatch_external_notifications(contact, session_data))


async def _dispatch_external_notifications(contact: OwnerContact, session_data: dict) -> None:
    try:
        await notification_manager.notify_ding(contact, session_data)
    except Exception:
        logger.exception(
            "Failed to dispatch external notifications for session %s",
            session_data.get("session_id"),
        )


# TODO: Add middleware for request logging
# TODO: Implement authentication middleware
# TODO: Add rate limiting middleware
# TODO: Configure database connections
# TODO: Add background tasks for session cleanup
