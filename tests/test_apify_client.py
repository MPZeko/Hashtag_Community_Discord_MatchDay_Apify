from __future__ import annotations

from typing import Any

from matchday_bot.apify_client import ApifyClient


class DummyResponse:
    def __init__(self, status_code: int, payload: Any) -> None:
        self.status_code = status_code
        self._payload = payload
        self.content = str(payload).encode()
        self.text = str(payload)

    def json(self) -> Any:
        return self._payload

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            raise RuntimeError(f"http {self.status_code}")


def test_apify_client_retries_with_empty_payload_after_400(monkeypatch) -> None:
    calls: list[dict[str, Any]] = []

    responses = [
        DummyResponse(400, {"error": "bad input"}),
        DummyResponse(200, [{"id": "ok"}]),
    ]

    def fake_post(
        url: str,
        params: dict[str, str],
        json: dict[str, Any],
        timeout: int,
    ) -> DummyResponse:
        calls.append(json)
        return responses.pop(0)

    import requests

    monkeypatch.setattr(requests, "post", fake_post)

    client = ApifyClient(token="x")
    items = client.run_actor_items("owner~actor", {"team": "Hashtag United"})

    assert items == [{"id": "ok"}]
    assert calls == [{"team": "Hashtag United"}, {}]


def test_apify_client_falls_back_to_runs_endpoint_when_sync_400(monkeypatch) -> None:
    def fake_post(
        url: str,
        params: dict[str, str],
        json: dict[str, Any],
        timeout: int,
    ) -> DummyResponse:
        return DummyResponse(400, {"error": "unsupported endpoint"})

    import requests

    monkeypatch.setattr(requests, "post", fake_post)

    client = ApifyClient(token="x")

    def fake_runs_fallback(
        requests_mod: Any,
        actor_id: str,
        payload: dict[str, Any],
    ) -> list[dict[str, Any]]:
        assert actor_id == "owner~actor"
        assert payload == {}
        return [{"id": "from-fallback"}]

    monkeypatch.setattr(client, "_run_via_runs_endpoint", fake_runs_fallback)

    items = client.run_actor_items("owner~actor", {})

    assert items == [{"id": "from-fallback"}]
