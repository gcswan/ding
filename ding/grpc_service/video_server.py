"""
gRPC Video Streaming Server for Ding Doorbell App

This server facilitates video chat sessions between door visitors and door owners.
It acts as a relay/bridge between two mobile clients, handling the video streaming
and session management.

ARCHITECTURE OVERVIEW:
- Bidirectional streaming for real-time video communication
- Session-based communication (each doorbell interaction creates a session)
- Concurrent handling of multiple video chat sessions
- TODO: Add WebRTC integration for peer-to-peer optimization
- TODO: Implement TURN/STUN servers for NAT traversal
- TODO: Add recording capabilities for security purposes
"""

import asyncio
import logging
from typing import Dict, Set
from concurrent import futures
import grpc

# Import generated gRPC classes
from . import video_stream_pb2
from . import video_stream_pb2_grpc

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class VideoStreamServicer(video_stream_pb2_grpc.VideoStreamServiceServicer):
    """
    Main video streaming service that handles bidirectional video communication.

    This servicer manages video chat sessions between two clients:
    - Client A: Door visitor (person who scanned QR code)
    - Client B: Door owner (person who owns the doorbell)

    TODO: Implement proper authentication and authorization
    TODO: Add rate limiting to prevent abuse
    TODO: Implement session timeouts and cleanup
    TODO: Add metrics and monitoring
    """

    def __init__(self):
        # Active video sessions: session_id -> set of client streams
        self.active_sessions: Dict[str, Set] = {}
        # Client mapping: session_id -> {client_id: stream}
        self.session_clients: Dict[str, Dict[str, any]] = {}

        # TODO: Add Redis or another persistent store for session management
        # TODO: Implement session persistence across server restarts
        # TODO: Add cleanup mechanism for abandoned sessions

    async def VideoChat(self, request_iterator, context):
        """
        Bidirectional video streaming endpoint.

        This method handles the core video chat functionality:
        1. Receives video frames from one client
        2. Relays them to the other client in the same session
        3. Manages session state and cleanup

        TODO: Add video quality adaptation based on network conditions
        TODO: Implement frame buffering for smoother playback
        TODO: Add support for multiple video formats/codecs
        """
        client_session_id = None
        client_id = None

        try:
            async for video_frame in request_iterator:
                session_id = video_frame.session_id
                sender_client_id = video_frame.client_id

                # Initialize session tracking
                if client_session_id is None:
                    client_session_id = session_id
                    client_id = sender_client_id
                    logger.info(f"Client {client_id} joined session {session_id}")

                    # TODO: Validate session exists and client is authorized
                    # TODO: Check if session has room for another client

                    # Initialize session data structures
                    if session_id not in self.active_sessions:
                        self.active_sessions[session_id] = set()
                        self.session_clients[session_id] = {}

                    # Add client to session
                    self.session_clients[session_id][client_id] = context
                    self.active_sessions[session_id].add(client_id)

                # Relay video frame to other clients in the session
                await self._relay_video_frame(video_frame, sender_client_id)

                # TODO: Add frame rate limiting
                # TODO: Implement video quality metrics collection
                # TODO: Add frame validation and security checks

        except grpc.RpcError as e:
            logger.error(f"gRPC error in VideoChat: {e}")
        except Exception as e:
            logger.error(f"Unexpected error in VideoChat: {e}")
        finally:
            # Cleanup when client disconnects
            await self._cleanup_client(client_session_id, client_id)

    async def SessionControl(self, request_iterator, context):
        """
        Handles control messages for video sessions.

        Control messages include:
        - JOIN_SESSION: Client wants to join a session
        - LEAVE_SESSION: Client is leaving
        - HEARTBEAT: Keepalive messages
        - SESSION_READY: Both clients are ready to start

        TODO: Implement comprehensive session state machine
        TODO: Add session recording controls
        TODO: Implement emergency session termination
        """
        try:
            async for control_msg in request_iterator:
                session_id = control_msg.session_id
                client_id = control_msg.client_id
                control_type = control_msg.control_type

                logger.info(f"Control message: {control_type} from {client_id} in session {session_id}")

                if control_type == video_stream_pb2.ControlType.JOIN_SESSION:
                    # TODO: Implement proper session joining logic
                    # TODO: Notify other clients in session
                    response = video_stream_pb2.ControlMessage(
                        session_id=session_id,
                        client_id="server",
                        control_type=video_stream_pb2.ControlType.SESSION_READY,
                        message="Welcome to the session"
                    )
                    yield response

                elif control_type == video_stream_pb2.ControlType.LEAVE_SESSION:
                    # TODO: Implement proper session leaving logic
                    # TODO: Notify other clients
                    await self._cleanup_client(session_id, client_id)

                elif control_type == video_stream_pb2.ControlType.HEARTBEAT:
                    # TODO: Update client's last seen timestamp
                    # TODO: Respond with server heartbeat
                    pass

                # TODO: Handle other control types
                # TODO: Add session state validation

        except Exception as e:
            logger.error(f"Error in SessionControl: {e}")

    async def _relay_video_frame(self, video_frame: video_stream_pb2.VideoFrame, sender_id: str):
        """
        Relay a video frame to all other clients in the session.

        TODO: Implement smart relaying (don't send back to sender)
        TODO: Add frame transformation/transcoding if needed
        TODO: Implement selective forwarding for multi-party calls
        """
        session_id = video_frame.session_id

        if session_id not in self.session_clients:
            logger.warning(f"Attempted to relay frame to non-existent session: {session_id}")
            return

        # Send to all other clients in the session
        for client_id, client_context in self.session_clients[session_id].items():
            if client_id != sender_id:  # Don't send back to sender
                try:
                    # TODO: This is a placeholder - implement actual frame relaying
                    # In a real implementation, you'd use the client_context to send data
                    logger.debug(f"Relaying frame from {sender_id} to {client_id}")
                except Exception as e:
                    logger.error(f"Failed to relay frame to client {client_id}: {e}")
                    # TODO: Remove failed clients from session

    async def _cleanup_client(self, session_id: str, client_id: str):
        """
        Clean up client data when they disconnect.

        TODO: Implement graceful session cleanup
        TODO: Notify remaining clients about disconnection
        TODO: Save session metadata for analytics
        """
        if not session_id or not client_id:
            return

        logger.info(f"Cleaning up client {client_id} from session {session_id}")

        # Remove from session tracking
        if session_id in self.session_clients:
            self.session_clients[session_id].pop(client_id, None)

        if session_id in self.active_sessions:
            self.active_sessions[session_id].discard(client_id)

            # If session is empty, clean it up
            if not self.active_sessions[session_id]:
                del self.active_sessions[session_id]
                del self.session_clients[session_id]
                logger.info(f"Session {session_id} cleaned up - no more clients")


async def serve():
    """
    Start the gRPC video streaming server.

    TODO: Add TLS/SSL configuration for production
    TODO: Implement health checks
    TODO: Add server metrics and monitoring
    TODO: Configure for horizontal scaling
    """
    server = grpc.aio.server(futures.ThreadPoolExecutor(max_workers=10))
    video_stream_pb2_grpc.add_VideoStreamServiceServicer_to_server(
        VideoStreamServicer(), server
    )

    # TODO: Configure server address from environment variables
    listen_addr = '[::]:50051'
    server.add_insecure_port(listen_addr)

    logger.info(f"Starting gRPC video server on {listen_addr}")
    await server.start()

    # TODO: Add graceful shutdown handling
    try:
        await server.wait_for_termination()
    except KeyboardInterrupt:
        logger.info("Server interrupted, shutting down...")
        await server.stop(grace=5)


if __name__ == '__main__':
    asyncio.run(serve())