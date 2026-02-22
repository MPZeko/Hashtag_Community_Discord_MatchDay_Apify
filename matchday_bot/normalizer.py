from __future__ import annotations

import hashlib
import json
import logging
from datetime import datetime, timezone
from typing import Any

from .models import GoalEvent, Match, MatchStatus

logger = logging.getLogger(__name__)

STATUS_MAP = {
    "scheduled": MatchStatus.SCHEDULED,
    "notstarted": MatchStatus.SCHEDULED,
    "ns": MatchStatus.SCHEDULED,
    "live": MatchStatus.LIVE,
    "inprogress": MatchStatus.LIVE,
    "1h": MatchStatus.LIVE,
    "2h": MatchStatus.LIVE,
    "ht": MatchStatus.HT,
    "halftime": MatchStatus.HT,
    "ft": MatchStatus.FT,
    "fulltime": MatchStatus.FT,
    "finished": MatchStatus.FT,
    "postponed": MatchStatus.POSTPONED,
}


def _coalesce(data: dict[str, Any], keys: list[str], default: Any = None) -> Any:
    for key in keys:
        if key in data and data[key] is not None:
            return data[key]
    return default


def _parse_kickoff(value: Any) -> datetime:
    if isinstance(value, (int, float)):
        return datetime.fromtimestamp(float(value), tz=timezone.utc)
    if isinstance(value, str):
        text = value.replace("Z", "+00:00")
        parsed = datetime.fromisoformat(text)
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        return parsed
    raise ValueError("Missing kickoff timestamp")


def _normalize_status(value: Any) -> MatchStatus:
    text = str(value or "").strip().lower()
    return STATUS_MAP.get(text, MatchStatus.UNKNOWN)


def _minute_int(v: Any) -> int | None:
    try:
        return int(v)
    except (TypeError, ValueError):
        return None


def _event_id(event: dict[str, Any]) -> str:
    raw = _coalesce(event, ["id", "eventId", "event_id"])
    if raw:
        return str(raw)
    stable = json.dumps(
        {
            "team": _coalesce(event, ["team", "teamName", "team_name"], ""),
            "player": _coalesce(event, ["player", "playerName", "player_name"], ""),
            "minute": _coalesce(event, ["minute", "time", "elapsed"], ""),
            "added": _coalesce(event, ["addedTime", "added", "extraTime"], ""),
            "pen": _coalesce(event, ["isPenalty", "penalty"], False),
            "og": _coalesce(event, ["isOwnGoal", "ownGoal", "owngoal"], False),
        },
        sort_keys=True,
    )
    return hashlib.sha1(stable.encode()).hexdigest()[:16]


def _parse_events(raw: Any) -> list[GoalEvent]:
    events: list[dict[str, Any]] = []
    if isinstance(raw, dict):
        for key in ("events", "goals", "goalEvents", "homeGoals", "awayGoals"):
            value = raw.get(key)
            if isinstance(value, list):
                events.extend([x for x in value if isinstance(x, dict)])
    elif isinstance(raw, list):
        events = [x for x in raw if isinstance(x, dict)]

    parsed: list[GoalEvent] = []
    seen: set[str] = set()
    for event in events:
        minute = _minute_int(_coalesce(event, ["minute", "time", "elapsed"]))
        if minute is None:
            continue
        eid = _event_id(event)
        if eid in seen:
            continue
        seen.add(eid)
        parsed.append(
            GoalEvent(
                event_id=eid,
                team=str(_coalesce(event, ["team", "teamName", "team_name"], "Unknown")),
                player_name=str(
                    _coalesce(event, ["player", "playerName", "player_name"], "Unknown")
                ),
                minute=minute,
                added_time=_minute_int(_coalesce(event, ["addedTime", "added", "extraTime"])),
                is_penalty=bool(_coalesce(event, ["isPenalty", "penalty"], False)),
                is_own_goal=bool(_coalesce(event, ["isOwnGoal", "ownGoal", "owngoal"], False)),
            )
        )
    return sorted(parsed, key=lambda e: (e.minute, e.added_time or 0, e.event_id))


def normalize_match(raw: dict[str, Any]) -> Match:
    kickoff = _parse_kickoff(
        _coalesce(raw, ["startTimestamp", "kickoff", "kickoffTime", "utcTime"])
    )
    match_id = str(_coalesce(raw, ["id", "matchId", "fixtureId", "eventId"], "unknown-match"))
    home = str(_coalesce(raw, ["homeTeam", "home", "home_name"], "Home"))
    away = str(_coalesce(raw, ["awayTeam", "away", "away_name"], "Away"))

    competition = _coalesce(raw, ["competition", "tournament", "league"], "Unknown competition")
    if isinstance(competition, dict):
        competition = _coalesce(competition, ["name", "title"], "Unknown competition")

    round_raw = _coalesce(raw, ["round", "roundInfo", "stage"])
    if isinstance(round_raw, dict):
        round_raw = _coalesce(round_raw, ["name", "round", "num"])

    return Match(
        match_id=match_id,
        home_team=home,
        away_team=away,
        competition_name=str(competition),
        round_name_or_number=str(round_raw) if round_raw is not None else None,
        kickoff=kickoff,
        status=_normalize_status(_coalesce(raw, ["status", "state", "matchStatus"])),
        home_score=int(_coalesce(raw, ["homeScore", "home_score", "scoreHome"], 0) or 0),
        away_score=int(_coalesce(raw, ["awayScore", "away_score", "scoreAway"], 0) or 0),
        minute=_minute_int(_coalesce(raw, ["minute", "time", "elapsed"])),
        added_time=_minute_int(_coalesce(raw, ["addedTime", "extraTime"])),
        events=_parse_events(raw),
    )


def choose_next_match(items: list[dict[str, Any]], team_name: str) -> Match:
    matches: list[Match] = []
    for item in items:
        if not isinstance(item, dict):
            continue
        try:
            match = normalize_match(item)
        except Exception:
            logger.warning("schema mismatch while normalizing item", exc_info=True)
            continue
        teams = f"{match.home_team} {match.away_team}".lower()
        if team_name.lower() in teams:
            matches.append(match)
    if not matches:
        raise ValueError("No match found for configured team")
    return sorted(matches, key=lambda m: m.kickoff)[0]


def redact_for_debug(raw: dict[str, Any]) -> dict[str, Any]:
    redacted = dict(raw)
    for key in ["token", "authorization", "apiKey", "api_key"]:
        if key in redacted:
            redacted[key] = "***"
    return redacted
