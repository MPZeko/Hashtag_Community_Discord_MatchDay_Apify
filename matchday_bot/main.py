from __future__ import annotations

import argparse
import json
import logging
from datetime import datetime, timedelta, timezone
from uuid import uuid4

from .apify_client import ApifyClient
from .config import configure_logging, load_settings
from .discord_webhook import DiscordWebhookClient
from .formatting import (
    build_post_key,
    format_countdown,
    format_full_time,
    format_live,
    format_next_match,
)
from .models import MatchStatus
from .normalizer import choose_next_match, redact_for_debug
from .state_store import StateStore

logger = logging.getLogger(__name__)


def in_fast_window(
    now: datetime,
    kickoff: datetime,
    before_minutes: int,
    expected_duration: int,
    after_minutes: int,
) -> bool:
    start = kickoff - timedelta(minutes=before_minutes)
    end = kickoff + timedelta(minutes=expected_duration + after_minutes)
    return start <= now <= end


def _send(message: str, dry_run: bool, client: DiscordWebhookClient) -> None:
    if dry_run:
        logger.info("dry-run: would post message\n%s", message)
        return
    client.send(message)


def run(mode: str, dry_run: bool, dump_raw: bool) -> None:
    run_id = str(uuid4())
    settings = load_settings()
    configure_logging(settings.log_level, run_id)

    store = StateStore()
    state = store.load()
    now = datetime.now(tz=timezone.utc)

    logger.info("mode=%s now=%s", mode, now.isoformat())

    kickoff = None
    if state.next_match_kickoff_iso:
        kickoff = datetime.fromisoformat(state.next_match_kickoff_iso.replace("Z", "+00:00"))

    if mode == "fast" and kickoff is not None:
        allowed = in_fast_window(
            now,
            kickoff,
            settings.fast_window_before_minutes,
            settings.expected_match_duration_minutes,
            settings.fast_window_after_minutes,
        )
        logger.info("fast-window kickoff=%s allowed=%s", kickoff.isoformat(), allowed)
        if not allowed:
            return

    apify = ApifyClient(settings.apify_api_token)
    webhook = DiscordWebhookClient(settings.discord_webhook_url)
    items = apify.run_actor_items(settings.apify_actor_id, settings.apify_input)

    if dump_raw and items:
        raw_item = json.dumps(redact_for_debug(items[0]), ensure_ascii=False)[:3000]
        logger.info("raw_item=%s", raw_item)

    match = choose_next_match(items, settings.team_name)

    if mode == "slow":
        state.next_match_id = match.match_id
        state.next_match_kickoff_iso = match.kickoff.isoformat()
        threshold = match.kickoff - timedelta(hours=settings.prematch_window_hours)
        if now >= threshold and state.posted_next_match_for_match_id != match.match_id:
            _send(format_next_match(match, settings.timezone), dry_run, webhook)
            state.posted_next_match_for_match_id = match.match_id
        store.save(state)
        return

    seen = set(state.last_seen_event_ids_by_match_id.get(match.match_id, []))
    new_goals = [event for event in match.events if event.event_id not in seen]

    countdown_bucket = None
    if now < match.kickoff:
        remaining_minutes = max(0, int((match.kickoff - now).total_seconds() // 60))
        countdown_bucket = remaining_minutes // 5
        message = format_countdown(match, settings.timezone, remaining_minutes)
    else:
        message = format_live(match, new_goals)

    last_goal_event_id = match.events[-1].event_id if match.events else None
    post_key = build_post_key(match, countdown_bucket, last_goal_event_id)
    last_key = state.last_fast_post_key_by_match_id.get(match.match_id)

    logger.info(
        "fast decision match_id=%s post_key=%s last_key=%s",
        match.match_id,
        post_key,
        last_key,
    )
    if post_key != last_key:
        _send(message, dry_run, webhook)
        state.last_fast_post_key_by_match_id[match.match_id] = post_key

    if new_goals:
        seen.update(event.event_id for event in new_goals)
        state.last_seen_event_ids_by_match_id[match.match_id] = sorted(seen)

    if match.status == MatchStatus.FT and state.posted_full_time_for_match_id != match.match_id:
        _send(format_full_time(match, settings.timezone), dry_run, webhook)
        state.posted_full_time_for_match_id = match.match_id

    store.save(state)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=["slow", "fast"], required=True)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--dump-raw", action="store_true")
    args = parser.parse_args()
    run(mode=args.mode, dry_run=args.dry_run, dump_raw=args.dump_raw)


if __name__ == "__main__":
    main()
