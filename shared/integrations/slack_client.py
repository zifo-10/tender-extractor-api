"""Slack webhook integration for alerting."""
from __future__ import annotations

import logging
from typing import Optional

import requests
from django.conf import settings

logger = logging.getLogger(__name__)


class SlackWebhookClient:
    """Sends alert messages to a Slack channel via an Incoming Webhook."""

    def __init__(self, webhook_url: Optional[str] = None) -> None:
        self._webhook_url: str = webhook_url or getattr(settings, "SLACK_WEBHOOK_URL", "")

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def send_alert(self, message: str, *, level: str = "warning") -> bool:
        """Send a plain-text alert.  Returns True on success, False otherwise."""
        if not self._webhook_url:
            logger.debug("Slack webhook URL not configured — skipping alert.")
            return False

        emoji_map = {"info": ":information_source:", "warning": ":warning:", "error": ":red_circle:"}
        emoji = emoji_map.get(level, ":warning:")
        payload = {"text": f"{emoji} *Tender Extractor API Alert*\n{message}"}

        try:
            response = requests.post(
                self._webhook_url,
                json=payload,
                timeout=5,
            )
            if response.status_code != 200:
                logger.warning(
                    "Slack webhook returned non-200",
                    extra={"status_code": response.status_code},
                )
                return False
            return True
        except requests.RequestException as exc:
            logger.warning("Failed to send Slack alert", extra={"error": str(exc)})
            return False

    def alert_all_providers_failed(self, request_id: str, user: str) -> None:
        self.send_alert(
            f"All LLM providers failed.\n• request_id: `{request_id}`\n• user: `{user}`",
            level="error",
        )

    def alert_unexpected_exception(self, request_id: str, error: str) -> None:
        self.send_alert(
            f"Unexpected exception in tender extractor.\n• request_id: `{request_id}`\n• error: `{error}`",
            level="error",
        )


# Module-level singleton
slack_client = SlackWebhookClient()
