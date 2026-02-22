from __future__ import annotations

import logging
import time

logger = logging.getLogger(__name__)


class DiscordWebhookClient:
    def __init__(self, webhook_url: str, timeout_seconds: int = 10) -> None:
        self.webhook_url = webhook_url
        self.timeout_seconds = timeout_seconds

    def send(self, content: str) -> None:
        import requests

        max_retries = 3
        for attempt in range(1, max_retries + 1):
            response = requests.post(
                self.webhook_url,
                json={"content": content},
                timeout=self.timeout_seconds,
            )
            snippet = response.text[:200].replace("\n", " ")
            logger.info("discord status=%s response=%s", response.status_code, snippet)
            if response.status_code == 429 and attempt < max_retries:
                retry_after = float(response.headers.get("Retry-After", "1"))
                time.sleep(max(retry_after, 1.0))
                continue
            response.raise_for_status()
            return
