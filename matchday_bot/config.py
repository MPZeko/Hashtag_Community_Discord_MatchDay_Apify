from __future__ import annotations

import json
import logging
import os
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class Settings:
    discord_webhook_url: str
    apify_api_token: str
    apify_actor_id: str
    apify_input: dict[str, Any]
    team_name: str
    timezone: str
    prematch_window_hours: int
    fast_window_before_minutes: int
    fast_window_after_minutes: int
    expected_match_duration_minutes: int
    log_level: str


def _env_int(name: str, default: int) -> int:
    value = os.getenv(name)
    if value is None:
        return default
    try:
        return int(value)
    except ValueError as exc:
        raise ValueError(f"Environment variable {name} must be int") from exc


def _env_json(name: str, default: dict[str, Any]) -> dict[str, Any]:
    raw = os.getenv(name)
    if not raw:
        return default
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ValueError(f"Environment variable {name} must be valid JSON") from exc
    if not isinstance(parsed, dict):
        raise ValueError(f"Environment variable {name} must be a JSON object")
    return parsed


def load_settings() -> Settings:
    webhook = os.getenv("DISCORD_WEBHOOK_URL", "").strip()
    token = os.getenv("APIFY_API_TOKEN", "").strip()
    actor_id = os.getenv("APIFY_ACTOR_ID", "").strip()

    missing = [
        name
        for name, value in (
            ("DISCORD_WEBHOOK_URL", webhook),
            ("APIFY_API_TOKEN", token),
            ("APIFY_ACTOR_ID", actor_id),
        )
        if not value
    ]
    if missing:
        raise ValueError(f"Missing required environment variables: {', '.join(missing)}")

    return Settings(
        discord_webhook_url=webhook,
        apify_api_token=token,
        apify_actor_id=actor_id,
        apify_input=_env_json("APIFY_INPUT_JSON", {"team": "Hashtag United"}),
        team_name=os.getenv("TEAM_NAME", "Hashtag United"),
        timezone=os.getenv("TIMEZONE", "Europe/London"),
        prematch_window_hours=_env_int("PREMATCH_WINDOW_HOURS", 24),
        fast_window_before_minutes=_env_int("FAST_WINDOW_BEFORE_MINUTES", 60),
        fast_window_after_minutes=_env_int("FAST_WINDOW_AFTER_MINUTES", 30),
        expected_match_duration_minutes=_env_int("EXPECTED_MATCH_DURATION_MINUTES", 120),
        log_level=os.getenv("LOG_LEVEL", "INFO").upper(),
    )


def configure_logging(level: str, run_id: str) -> None:
    logging.basicConfig(
        level=level,
        format=f"%(asctime)s %(levelname)s run_id={run_id} %(name)s: %(message)s",
    )
