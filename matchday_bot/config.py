from __future__ import annotations

import json
import logging
import os
import re
from dataclasses import dataclass
from typing import Any
from urllib.parse import parse_qs


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


def _normalize_actor_ref(actor_ref: str) -> str:
    cleaned = actor_ref.strip()
    if "/" in cleaned and "~" not in cleaned:
        owner, name = cleaned.split("/", 1)
        cleaned = f"{owner}~{name}"
    if "~" not in cleaned:
        raise ValueError("Invalid APIFY_ACTOR_ID format. Expected owner~name.")
    owner, name = cleaned.split("~", 1)
    if not owner.strip() or not name.strip():
        raise ValueError("Invalid APIFY_ACTOR_ID format. Expected owner~name.")
    return f"{owner.strip()}~{name.strip()}"


def parse_apify_actor_ref(raw: str) -> tuple[str, str | None]:
    value = raw.strip()

    token: str | None = None

    if "?" in value:
        prefix, query = value.split("?", 1)
        token_qs = parse_qs(query).get("token")
        if token_qs:
            token = token_qs[0].strip() or None
        value = prefix.strip()

    if "|" in value:
        prefix, suffix = value.split("|", 1)
        value = prefix.strip()
        suffix_token = suffix.strip()
        if suffix_token.lower().startswith("token="):
            suffix_token = suffix_token.split("=", 1)[1].strip()
        token = token or (suffix_token or None)

    semicolon_match = re.match(r"^(?P<actor>[^;]+);\s*token=(?P<token>.+)$", value, re.IGNORECASE)
    if semicolon_match:
        value = semicolon_match.group("actor").strip()
        token = token or semicolon_match.group("token").strip() or None

    space_match = re.match(r"^(?P<actor>.+?)\s+token=(?P<token>.+)$", value, re.IGNORECASE)
    if space_match:
        value = space_match.group("actor").strip()
        token = token or space_match.group("token").strip() or None

    actor_ref = _normalize_actor_ref(value)
    return actor_ref, token


def load_settings() -> Settings:
    webhook = os.getenv("DISCORD_WEBHOOK_URL", "").strip()
    actor_raw = os.getenv("APIFY_ACTOR_ID", "").strip()

    missing = [
        name
        for name, value in (
            ("DISCORD_WEBHOOK_URL", webhook),
            ("APIFY_ACTOR_ID", actor_raw),
        )
        if not value
    ]
    if missing:
        raise ValueError(f"Missing required environment variables: {', '.join(missing)}")

    actor_id, embedded_token = parse_apify_actor_ref(actor_raw)
    token = os.getenv("APIFY_API_TOKEN", "").strip() or embedded_token
    if not token:
        raise ValueError(
            "Missing Apify API token. Set APIFY_API_TOKEN secret or embed token in APIFY_ACTOR_ID."
        )

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
