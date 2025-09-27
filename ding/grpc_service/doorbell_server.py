"""
gRPC Doorbell Service for QR Code Scanning and Notifications

This service handles the doorbell functionality:
- QR code scanning events
- Push notifications to door owners
- Session initiation for video chats
- Response handling from door owners

ARCHITECTURE OVERVIEW:
- Handles QR code scan events from mobile clients
- Manages notification delivery to door owners
- Coordinates with video streaming service for chat sessions
- TODO: Integrate with push notification services (FCM, APNs)
- TODO: Add user management and authentication
- TODO: Implement persistent session storage
"""

import asyncio
import logging
import uuid
from typing import Dict, Set
from concurrent import futures
import grpc

# Import generated gRPC classes
from . import doorbell_pb2
from . import doorbell_pb2_grpc

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DoorbellServicer(doorbell_pb2_grpc.DoorbellServiceServicer):
    """
    Main doorbell service that handles QR code scanning and notifications.

    This servicer manages the doorbell workflow:
    1. QR code scanning by visitors
    2. Notification delivery to door owners
    3. Response collection from door owners
    4. Session initiation for video chats

    TODO: Implement proper user authentication
    TODO: Add rate limiting and abuse prevention
    TODO: Integrate with external notification services
    TODO: Add analytics and usage tracking
    """

    def __init__(self):
        # Active notification streams: door_owner_id -> stream context
        self.notification_streams: Dict[str, any] = {}
        # Pending dings: session_id -> ding metadata
        self.pending_dings: Dict[str, Dict] = {}
        # QR code mappings: qr_code_id -> door_owner_id
        self.qr_code_mappings: Dict[str, str] = {}

        # TODO: Replace with proper database/Redis storage
        # TODO: Add session persistence and recovery
        # TODO: Implement proper user management

        # Sample QR codes for testing
        # TODO: Remove these and implement proper QR code management
        self.qr_code_mappings.update({
            "qr_test_001": "owner_alice",
            "qr_test_002": "owner_bob",
        })

    async def ScanQRCode(self, request, context):
        """
        Handle QR code scan events from mobile devices.

        When someone scans a QR code:
        1. Validate the QR code
        2. Create a new session
        3. Send notification to door owner
        4. Return session info to scanner

        TODO: Add QR code validation and security checks
        TODO: Implement location-based verification
        TODO: Add spam protection and rate limiting
        """
        qr_code_id = request.qr_code_id
        scanner_device_id = request.scanner_device_id
        timestamp = request.timestamp

        logger.info(f"QR code scan: {qr_code_id} by device {scanner_device_id}")

        # Validate QR code
        if qr_code_id not in self.qr_code_mappings:
            logger.warning(f"Invalid QR code scanned: {qr_code_id}")
            return doorbell_pb2.ScanResponse(
                success=False,
                message="Invalid QR code",
                session_id="",
                door_owner_id=""
            )

        door_owner_id = self.qr_code_mappings[qr_code_id]
        session_id = str(uuid.uuid4())

        # Store pending ding
        self.pending_dings[session_id] = {
            "door_owner_id": door_owner_id,
            "scanner_device_id": scanner_device_id,
            "qr_code_id": qr_code_id,
            "timestamp": timestamp,
            "status": "pending"
        }

        # Send notification to door owner
        await self._send_notification_to_owner(
            door_owner_id=door_owner_id,
            session_id=session_id,
            scanner_device_id=scanner_device_id,
            notification_type=doorbell_pb2.NotificationType.DING_REQUEST
        )

        # TODO: Set up session timeout
        # TODO: Add session cleanup mechanism

        return doorbell_pb2.ScanResponse(
            success=True,
            message="QR code scanned successfully. Door owner has been notified.",
            session_id=session_id,
            door_owner_id=door_owner_id
        )

    async def NotificationStream(self, request, context):
        """
        Establish a persistent notification stream for door owners.

        Door owners connect to this stream to receive real-time notifications
        about QR code scans and ding requests.

        TODO: Implement proper authentication for door owners
        TODO: Add notification filtering and preferences
        TODO: Implement push notification fallback
        """
        door_owner_id = request.door_owner_id
        device_token = request.device_token

        logger.info(f"Door owner {door_owner_id} connected for notifications")

        # Store the stream for this door owner
        self.notification_streams[door_owner_id] = context

        try:
            # Keep the stream alive and handle disconnections
            while True:
                # TODO: Implement heartbeat mechanism
                # TODO: Handle stream reconnection logic
                await asyncio.sleep(30)  # Heartbeat every 30 seconds

                # Send heartbeat notification
                heartbeat = doorbell_pb2.Notification(
                    notification_id=str(uuid.uuid4()),
                    door_owner_id=door_owner_id,
                    scanner_device_id="",
                    type=doorbell_pb2.NotificationType.DING_TIMEOUT,  # Using as heartbeat
                    message="heartbeat",
                    timestamp=int(asyncio.get_event_loop().time()),
                    session_id=""
                )
                yield heartbeat

        except grpc.RpcError:
            logger.info(f"Door owner {door_owner_id} disconnected from notifications")
        finally:
            # Clean up when door owner disconnects
            self.notification_streams.pop(door_owner_id, None)

    async def RespondToDing(self, request, context):
        """
        Handle door owner's response to a ding request.

        When a door owner responds to a ding:
        1. Update the session status
        2. Notify the scanner about the response
        3. If accepted, initiate video chat session
        4. Clean up if rejected

        TODO: Implement custom response messages
        TODO: Add response templates and quick replies
        TODO: Implement automatic responses based on time/location
        """
        session_id = request.session_id
        door_owner_id = request.door_owner_id
        response_type = request.response_type
        custom_message = request.custom_message

        logger.info(f"Door owner {door_owner_id} responded to session {session_id}: {response_type}")

        # Validate session exists
        if session_id not in self.pending_dings:
            return doorbell_pb2.ResponseResult(
                success=False,
                message="Invalid or expired session",
                video_session_id=""
            )

        session_data = self.pending_dings[session_id]

        # Update session status
        session_data["status"] = "responded"
        session_data["response_type"] = response_type
        session_data["response_message"] = custom_message

        if response_type == doorbell_pb2.ResponseType.ACCEPT:
            # Create video chat session
            video_session_id = f"video_{session_id}"

            # TODO: Initialize video chat session with video server
            # TODO: Send connection details to both clients
            # TODO: Set up video session timeout

            # Notify scanner that request was accepted
            # TODO: Implement actual notification to scanner device

            logger.info(f"Video session {video_session_id} created for session {session_id}")

            return doorbell_pb2.ResponseResult(
                success=True,
                message="Ding accepted. Video chat session starting.",
                video_session_id=video_session_id
            )

        else:
            # Request was rejected or deferred
            response_messages = {
                doorbell_pb2.ResponseType.REJECT: "Door owner declined the request",
                doorbell_pb2.ResponseType.BUSY: "Door owner is busy, please try later",
                doorbell_pb2.ResponseType.CUSTOM: custom_message or "Custom response"
            }

            message = response_messages.get(response_type, "Unknown response")

            # TODO: Notify scanner about rejection
            # TODO: Clean up session data

            return doorbell_pb2.ResponseResult(
                success=True,
                message=message,
                video_session_id=""
            )

    async def _send_notification_to_owner(self, door_owner_id: str, session_id: str,
                                         scanner_device_id: str, notification_type):
        """
        Send notification to door owner about a ding request.

        TODO: Implement push notification fallback if owner is offline
        TODO: Add notification sound and vibration preferences
        TODO: Include scanner location and device info
        """
        if door_owner_id not in self.notification_streams:
            logger.warning(f"Door owner {door_owner_id} not connected for notifications")
            # TODO: Send push notification instead
            return

        notification = doorbell_pb2.Notification(
            notification_id=str(uuid.uuid4()),
            door_owner_id=door_owner_id,
            scanner_device_id=scanner_device_id,
            type=notification_type,
            message="Someone is at your door and wants to talk!",
            timestamp=int(asyncio.get_event_loop().time()),
            session_id=session_id
        )

        try:
            # Send notification through the stream
            # Note: This is a simplified implementation
            # TODO: Implement proper stream message sending
            logger.info(f"Notification sent to {door_owner_id} for session {session_id}")
        except Exception as e:
            logger.error(f"Failed to send notification to {door_owner_id}: {e}")


async def serve():
    """
    Start the gRPC doorbell server.

    TODO: Add TLS/SSL configuration
    TODO: Implement health checks
    TODO: Add server metrics and monitoring
    TODO: Configure for load balancing
    """
    server = grpc.aio.server(futures.ThreadPoolExecutor(max_workers=10))
    doorbell_pb2_grpc.add_DoorbellServiceServicer_to_server(
        DoorbellServicer(), server
    )

    # TODO: Configure server address from environment variables
    listen_addr = '[::]:50052'
    server.add_insecure_port(listen_addr)

    logger.info(f"Starting gRPC doorbell server on {listen_addr}")
    await server.start()

    try:
        await server.wait_for_termination()
    except KeyboardInterrupt:
        logger.info("Server interrupted, shutting down...")
        await server.stop(grace=5)


if __name__ == '__main__':
    asyncio.run(serve())