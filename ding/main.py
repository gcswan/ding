"""Simplified entry point for the Ding application."""

import logging
import sys

import uvicorn

from .utils.config import get_config


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def run() -> None:
    """Run the FastAPI application using Uvicorn."""

    config = get_config()
    uvicorn.run(
        "ding.api.main:app",
        host=config.server.host,
        port=config.server.port,
        log_level=config.server.log_level,
        reload=config.server.reload,
    )


def cli_main() -> None:
    """Console entry point when calling `python -m ding`."""

    try:
        run()
    except KeyboardInterrupt:
        logger.info("Application stopped by user")
    except Exception as exc:  # pragma: no cover - defensive logging
        logger.error("Failed to start application: %s", exc)
        sys.exit(1)


if __name__ == "__main__":
    cli_main()
