"""
Main application entry point for the Ding Doorbell Server

This module coordinates the startup of both gRPC services and the FastAPI REST server.
It provides a unified entry point for running the complete doorbell application.

ARCHITECTURE OVERVIEW:
- Runs gRPC video streaming service on port 50051
- Runs gRPC doorbell service on port 50052
- Runs FastAPI REST API on port 8000
- Coordinates graceful shutdown of all services
- TODO: Add configuration management
- TODO: Implement service discovery and health monitoring
- TODO: Add containerization support (Docker)
"""

import asyncio
import logging
import signal
import sys
from typing import List
from concurrent.futures import ThreadPoolExecutor

import uvicorn

# Import our services
from .api.main import app as fastapi_app
from .grpc_service.video_server import serve as serve_video
from .grpc_service.doorbell_server import serve as serve_doorbell

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class DingApplication:
    """
    Main application class that manages all services.

    This class coordinates the startup, running, and shutdown of:
    - gRPC Video Streaming Service
    - gRPC Doorbell Service
    - FastAPI REST API

    TODO: Add service health monitoring
    TODO: Implement graceful degradation if services fail
    TODO: Add configuration file support
    TODO: Implement service restart capabilities
    """

    def __init__(self):
        self.services: List[asyncio.Task] = []
        self.shutdown_event = asyncio.Event()

        # TODO: Load configuration from file or environment
        self.config = {
            "grpc_video_port": 50051,
            "grpc_doorbell_port": 50052,
            "fastapi_host": "0.0.0.0",
            "fastapi_port": 8000,
            "log_level": "info"
        }

    async def start_services(self):
        """
        Start all application services concurrently.

        This method starts:
        1. gRPC Video Streaming Service
        2. gRPC Doorbell Service
        3. FastAPI REST API server

        TODO: Add service dependency checking
        TODO: Implement staged startup (database, then services)
        TODO: Add startup health checks
        """
        logger.info("Starting Ding Doorbell Application...")

        # Start gRPC services
        logger.info("Starting gRPC Video Streaming Service...")
        video_task = asyncio.create_task(
            serve_video(),
            name="grpc_video_service"
        )
        self.services.append(video_task)

        logger.info("Starting gRPC Doorbell Service...")
        doorbell_task = asyncio.create_task(
            serve_doorbell(),
            name="grpc_doorbell_service"
        )
        self.services.append(doorbell_task)

        # Start FastAPI server
        logger.info("Starting FastAPI REST API...")
        fastapi_task = asyncio.create_task(
            self._run_fastapi(),
            name="fastapi_service"
        )
        self.services.append(fastapi_task)

        logger.info("All services started successfully!")

        # TODO: Add service readiness checks
        # TODO: Implement service discovery registration

    async def _run_fastapi(self):
        """
        Run the FastAPI server using uvicorn.

        TODO: Add SSL/TLS configuration for production
        TODO: Configure worker processes for scaling
        TODO: Add request logging and metrics
        """
        config = uvicorn.Config(
            app=fastapi_app,
            host=self.config["fastapi_host"],
            port=self.config["fastapi_port"],
            log_level=self.config["log_level"],
            # TODO: Enable in production
            # ssl_keyfile="path/to/keyfile.pem",
            # ssl_certfile="path/to/certfile.pem",
        )

        server = uvicorn.Server(config)
        await server.serve()

    async def wait_for_shutdown(self):
        """
        Wait for shutdown signal and handle graceful shutdown.

        TODO: Add graceful session cleanup
        TODO: Implement data persistence before shutdown
        TODO: Add shutdown timeout handling
        """
        await self.shutdown_event.wait()
        logger.info("Shutdown signal received, stopping services...")

        # Cancel all running services
        for service in self.services:
            if not service.done():
                service.cancel()

        # Wait for services to complete
        if self.services:
            await asyncio.gather(*self.services, return_exceptions=True)

        logger.info("All services stopped successfully")

    def signal_handler(self, signum, frame):
        """Handle shutdown signals (SIGINT, SIGTERM)."""
        logger.info(f"Received signal {signum}, initiating shutdown...")
        self.shutdown_event.set()

    async def run(self):
        """
        Main application run method.

        This is the primary entry point that:
        1. Sets up signal handlers
        2. Starts all services
        3. Waits for shutdown
        4. Handles cleanup

        TODO: Add application metrics collection
        TODO: Implement configuration hot-reloading
        TODO: Add distributed tracing support
        """
        # Set up signal handlers for graceful shutdown
        for sig in [signal.SIGINT, signal.SIGTERM]:
            signal.signal(sig, self.signal_handler)

        try:
            # Start all services
            await self.start_services()

            # Wait for shutdown signal
            await self.wait_for_shutdown()

        except Exception as e:
            logger.error(f"Application error: {e}")
            raise
        finally:
            logger.info("Application shutdown complete")


async def main():
    """
    Application entry point.

    TODO: Add command-line argument parsing
    TODO: Implement different run modes (dev, prod, test)
    TODO: Add version information display
    """
    logger.info("Initializing Ding Doorbell Application...")

    app = DingApplication()

    try:
        await app.run()
    except KeyboardInterrupt:
        logger.info("Application interrupted by user")
    except Exception as e:
        logger.error(f"Application failed: {e}")
        sys.exit(1)


def cli_main():
    """
    CLI entry point for setuptools/pip installation.

    This function is used when the package is installed and run as:
    - `python -m ding`
    - `ding` (if console script is configured)

    TODO: Add CLI subcommands (start, stop, status, config)
    TODO: Implement configuration validation
    TODO: Add development mode with auto-reload
    """
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Application stopped by user")
    except Exception as e:
        logger.error(f"Failed to start application: {e}")
        sys.exit(1)


if __name__ == "__main__":
    cli_main()