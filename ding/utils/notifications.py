"""Notification utilities for SMS and Microsoft Teams messages."""

import asyncio
import logging
from typing import List

import httpx

from .config import NotificationConfig
from .store import OwnerContact


logger = logging.getLogger(__name__)


class NotificationManager:
    """Dispatch notifications to configured channels."""

    def __init__(self, config: NotificationConfig):
        self._config = config

    async def notify_ding(self, contact: OwnerContact, session: dict) -> None:
        """Send ding notification across enabled channels."""

        tasks = []

        sms_recipients = self._resolve_sms_recipients(contact)
        if sms_recipients:
            tasks.append(self._send_sms(sms_recipients, session))

        teams_webhook = self._resolve_teams_webhook(contact)
        if teams_webhook:
            tasks.append(self._send_teams(teams_webhook, session))

        if not tasks:
            logger.warning(
                "No notification channels configured for door owner %s",
                contact.door_owner_id,
            )
            return

        await asyncio.gather(*tasks, return_exceptions=True)

    def _resolve_sms_recipients(self, contact: OwnerContact) -> List[str]:
        if not self._config.sms_enabled:
            return []
        recipients = contact.sms_recipients or self._config.sms_default_recipients
        return [number for number in recipients if number]

    def _resolve_teams_webhook(self, contact: OwnerContact) -> str | None:
        if not self._config.teams_enabled:
            return None
        return contact.teams_webhook_url or self._config.teams_default_webhook

    async def _send_sms(self, recipients: List[str], session: dict) -> None:
        account_sid = self._config.twilio_account_sid
        auth_token = self._config.twilio_auth_token
        from_number = self._config.twilio_from_number

        if not all([account_sid, auth_token, from_number]):
            logger.error("Twilio configuration incomplete; skipping SMS notification")
            return

        message_body = _format_sms_body(session)
        url = f"https://api.twilio.com/2010-04-01/Accounts/{account_sid}/Messages.json"

        async with httpx.AsyncClient(timeout=10) as client:
            for recipient in recipients:
                data = {"From": from_number, "To": recipient, "Body": message_body}
                try:
                    response = await client.post(url, data=data, auth=(account_sid, auth_token))
                    response.raise_for_status()
                    logger.info("SMS notification queued for %s", recipient)
                except httpx.HTTPError as exc:
                    logger.error("Failed to send SMS to %s: %s", recipient, exc)

    async def _send_teams(self, webhook_url: str, session: dict) -> None:
        payload = {"text": _format_teams_message(session)}

        timeout = httpx.Timeout(self._config.teams_timeout_seconds)
        async with httpx.AsyncClient(timeout=timeout) as client:
            try:
                response = await client.post(webhook_url, json=payload)
                response.raise_for_status()
                logger.info("Teams notification sent for session %s", session["session_id"])
            except httpx.HTTPError as exc:
                logger.error("Failed to send Teams notification: %s", exc)


def _format_sms_body(session: dict) -> str:
    location_hint = session.get("scanner_location")
    base_message = "Someone is at the door."
    if location_hint:
        base_message += f" Location: {location_hint}."
    return (
        f"Ding alert for {session.get('door_owner_id', 'door owner')}. "
        f"Session {session['session_id']} from {session.get('scanner_device_id', 'unknown device')}. "
        f"{base_message}"
    )


def _format_teams_message(session: dict) -> str:
    details = [
        f"**New Ding Request**",
        f"- Session: {session['session_id']}",
        f"- Device: {session.get('scanner_device_id', 'unknown')}"
    ]
    if session.get("scanner_location"):
        details.append(f"- Location: {session['scanner_location']}")
    details.append("Respond in the Ding console to accept or decline.")
    return "\n".join(details)
