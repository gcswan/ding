# Ding - Doorbell Application

A modern doorbell application that lets visitors scan QR codes and notify door
owners through SMS, Microsoft Teams, and WebSocket updates.

## Overview

Ding focuses on a streamlined set of features:

- **QR Code Scanning**: Visitors initiate contact by scanning door-specific QR codes.
- **Real-time Notifications**: Door owners receive alerts via SMS, Teams, or active
  WebSocket connections.
- **REST API**: FastAPI powers the HTTP endpoints for mobile and web clients.
- **WebSocket Support**: Door owners can keep a browser tab open for live updates.

## Architecture

A single FastAPI service manages QR code lifecycle, session tracking, and outbound
notifications. State is kept in an in-memory store for simplicity, and outbound
channels are configurable through environment variables.

### FastAPI REST Server (Port 8000)

- Endpoints for QR creation, scan handling, responses, and session lookup.
- WebSocket endpoint for browser-based notifications.
- Integrations for SMS (Twilio-compatible) and Microsoft Teams webhooks.
- Source: `ding/api/main.py`

## Quick Start

### Prerequisites

- Python 3.12+
- [uv](https://github.com/astral-sh/uv) package manager

### Installation

```bash
# Install dependencies
uv sync

# Run the application
uv run python -m ding.main
```

## API Documentation

Once running, visit:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **Health Check**: http://localhost:8000/health

## Key Endpoints

- `POST /qr-codes` – Generate new QR codes and store owner contact preferences.
- `POST /scan` – Handle QR code scans and trigger notifications.
- `POST /respond` – Record door owner responses to active sessions.
- `GET /sessions/{id}` – Retrieve session information.
- `WS /ws/notifications/{owner_id}` – Receive live notifications in the browser.

## Workflow

1. **QR Code Generation**: Door owner requests a QR code via `/qr-codes`.
2. **QR Code Scanning**: Visitor scans and posts to `/scan`.
3. **Notification**: SMS/Teams messages and WebSocket updates alert the owner.
4. **Response**: Door owner replies through `/respond` to accept or decline.

## Configuration

Environment variables control runtime behavior:

```bash
# Server settings
DING_HOST=0.0.0.0
DING_PORT=8000
DING_LOG_LEVEL=info

# SMS settings
DING_SMS_ENABLED=true
DING_TWILIO_ACCOUNT_SID=AC123
DING_TWILIO_AUTH_TOKEN=secret
DING_TWILIO_FROM_NUMBER=+15555550100
DING_SMS_RECIPIENTS=+15555550101,+15555550102

# Microsoft Teams
DING_TEAMS_ENABLED=true
DING_TEAMS_WEBHOOK=https://outlook.office.com/webhook/...
DING_TEAMS_TIMEOUT=5

# Environment
DING_ENVIRONMENT=development
DING_DEBUG=true

# Doorbell settings
DING_QR_SCAN_BASE_URL=https://ding.app/scan
DING_ESTIMATED_RESPONSE_TIME_SECONDS=30
```

- `DING_QR_SCAN_BASE_URL` controls the base URL embedded in generated QR codes.
- `DING_ESTIMATED_RESPONSE_TIME_SECONDS` sets the default response-time hint returned after scans.

## Development Status

This is a prototype with many production gaps. Priority areas include:

- Authentication and authorization.
- Persistent storage for QR codes, sessions, and audit history.
- Delivery guarantees, retries, and metrics for outbound notifications.
- Request validation, rate limiting, and security hardening.
- Automated testing across the API and notification helpers.

## Project Structure

```
ding/
  api/
    main.py           # FastAPI routes and WebSocket handlers
  models/
    schemas.py        # Pydantic request/response models
  utils/
    config.py         # Configuration management
    notifications.py  # SMS and Teams notification helpers
    store.py          # In-memory state store
  main.py             # Application entry point
pyproject.toml        # Project configuration and dependencies
README.md             # Project documentation
```

## Contributing

Helpful contributions include:

1. **Security**: Authentication, authorization, and secure defaults.
2. **Notifications**: Additional channels, retries, and observability.
3. **Clients**: Mobile or web experiences for visitors and door owners.
4. **Infrastructure**: Deployment, monitoring, and automation.
5. **Testing**: Unit, integration, and end-to-end coverage.

---

**Note**: The application is a development prototype and is not ready for
production use without further hardening.
