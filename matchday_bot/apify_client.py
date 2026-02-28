from __future__ import annotations

import logging
import time
from typing import Any

logger = logging.getLogger(__name__)


class ApifyClient:
    def __init__(self, token: str, timeout_seconds: int = 30) -> None:
        self.token = token
        self.timeout_seconds = timeout_seconds

    def _post_items(
        self,
        requests_mod: Any,
        url: str,
        params: dict[str, str],
        payload: dict[str, Any],
    ) -> Any:
        return requests_mod.post(
            url,
            params=params,
            json=payload,
            timeout=self.timeout_seconds,
        )

    def _run_via_runs_endpoint(
        self,
        requests_mod: Any,
        actor_id: str,
        payload: dict[str, Any],
    ) -> list[dict[str, Any]]:
        run_resp = requests_mod.post(
            f"https://api.apify.com/v2/acts/{actor_id}/runs",
            params={"token": self.token},
            json=payload,
            timeout=self.timeout_seconds,
        )
        run_resp.raise_for_status()
        run_data = run_resp.json().get("data", {})

        run_id = str(run_data.get("id", ""))
        dataset_id = run_data.get("defaultDatasetId")
        status = str(run_data.get("status", ""))

        timeout_at = time.time() + 120
        terminal = {"SUCCEEDED", "FAILED", "ABORTED", "TIMED-OUT"}
        while (not dataset_id or status not in terminal) and time.time() < timeout_at:
            if not run_id:
                break
            poll = requests_mod.get(
                f"https://api.apify.com/v2/actor-runs/{run_id}",
                params={"token": self.token},
                timeout=self.timeout_seconds,
            )
            poll.raise_for_status()
            pdata = poll.json().get("data", {})
            dataset_id = dataset_id or pdata.get("defaultDatasetId")
            status = str(pdata.get("status", status))
            if status in {"SUCCEEDED", "FAILED", "ABORTED", "TIMED-OUT"}:
                break
            time.sleep(2)

        if status in {"FAILED", "ABORTED", "TIMED-OUT"}:
            raise RuntimeError(f"Apify run failed with status={status}")
        if not dataset_id:
            raise RuntimeError("Apify run did not provide defaultDatasetId")

        items_resp = requests_mod.get(
            f"https://api.apify.com/v2/datasets/{dataset_id}/items",
            params={"token": self.token, "format": "json", "clean": "true"},
            timeout=self.timeout_seconds,
        )
        items_resp.raise_for_status()
        items = items_resp.json()
        if not isinstance(items, list) or not items:
            raise ValueError("Apify returned empty dataset items")
        return items

    def run_actor_items(
        self,
        actor_id: str,
        actor_input: dict[str, Any],
        max_retries: int = 4,
    ) -> list[dict[str, Any]]:
        import requests

        url = f"https://api.apify.com/v2/acts/{actor_id}/run-sync-get-dataset-items"
        params = {"token": self.token, "format": "json", "clean": "true"}

        backoff = 1.0
        fallback_to_empty_input_done = False
        payload = dict(actor_input)

        for attempt in range(1, max_retries + 1):
            start = time.monotonic()
            try:
                response = self._post_items(requests, url, params, payload)
            except requests.RequestException:
                if attempt == max_retries:
                    raise
                time.sleep(backoff)
                backoff *= 2
                continue

            elapsed_ms = int((time.monotonic() - start) * 1000)
            logger.info(
                "apify response actor=%s status=%s elapsed_ms=%s size=%s",
                actor_id,
                response.status_code,
                elapsed_ms,
                len(response.content),
            )

            if response.status_code == 400 and payload and not fallback_to_empty_input_done:
                fallback_to_empty_input_done = True
                payload = {}
                logger.warning(
                    "Apify returned 400 for provided input; retrying once with empty input payload."
                )
                continue

            if response.status_code == 400:
                snippet = response.text[:200].replace("\n", " ")
                logger.warning(
                    "Apify run-sync endpoint returned 400; trying runs fallback. response=%s",
                    snippet,
                )
                return self._run_via_runs_endpoint(requests, actor_id, payload)

            if response.status_code in (429, 500, 502, 503, 504):
                if attempt == max_retries:
                    response.raise_for_status()
                time.sleep(backoff)
                backoff *= 2
                continue
            if 400 <= response.status_code < 500:
                response.raise_for_status()

            items = response.json()
            if not isinstance(items, list) or not items:
                raise ValueError("Apify returned empty dataset items")
            return items

        raise RuntimeError("Apify retries exhausted")
