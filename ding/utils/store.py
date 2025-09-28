"""In-memory state management for the Ding application."""

import asyncio
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, Optional


@dataclass
class OwnerContact:
    """Contact preferences for a door owner."""

    door_owner_id: str
    sms_recipients: list[str] = field(default_factory=list)
    teams_webhook_url: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class StateStore:
    """Simple async-safe in-memory store for QR codes and sessions."""

    def __init__(self) -> None:
        self._lock = asyncio.Lock()
        self._qr_codes: Dict[str, Dict[str, Any]] = {}
        self._sessions: Dict[str, Dict[str, Any]] = {}
        self._owner_contacts: Dict[str, OwnerContact] = {}
        self._websocket_connections: Dict[str, Any] = {}
        self.start_time = datetime.now()

    async def add_qr_code(self, qr_code_id: str, metadata: Dict[str, Any]) -> None:
        async with self._lock:
            self._qr_codes[qr_code_id] = metadata

    async def get_qr_code(self, qr_code_id: str) -> Optional[Dict[str, Any]]:
        async with self._lock:
            return self._qr_codes.get(qr_code_id)

    async def add_session(self, session_id: str, session_data: Dict[str, Any]) -> None:
        async with self._lock:
            self._sessions[session_id] = session_data

    async def update_session(self, session_id: str, updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        async with self._lock:
            session = self._sessions.get(session_id)
            if not session:
                return None
            session.update(updates)
            return session

    async def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        async with self._lock:
            return self._sessions.get(session_id)

    async def set_owner_contact(self, contact: OwnerContact) -> None:
        async with self._lock:
            self._owner_contacts[contact.door_owner_id] = contact

    async def get_owner_contact(self, door_owner_id: str) -> Optional[OwnerContact]:
        async with self._lock:
            return self._owner_contacts.get(door_owner_id)

    async def add_websocket(self, door_owner_id: str, websocket: Any) -> None:
        async with self._lock:
            self._websocket_connections[door_owner_id] = websocket

    async def pop_websocket(self, door_owner_id: str) -> Optional[Any]:
        async with self._lock:
            return self._websocket_connections.pop(door_owner_id, None)

    async def get_websocket(self, door_owner_id: str) -> Optional[Any]:
        async with self._lock:
            return self._websocket_connections.get(door_owner_id)


store = StateStore()
