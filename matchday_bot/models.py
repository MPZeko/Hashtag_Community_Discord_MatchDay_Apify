from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


class MatchStatus(str, Enum):
    SCHEDULED = "SCHEDULED"
    LIVE = "LIVE"
    HT = "HT"
    FT = "FT"
    POSTPONED = "POSTPONED"
    UNKNOWN = "UNKNOWN"


@dataclass(frozen=True)
class GoalEvent:
    event_id: str
    team: str
    player_name: str
    minute: int
    added_time: int | None = None
    is_penalty: bool = False
    is_own_goal: bool = False


@dataclass(frozen=True)
class Match:
    match_id: str
    home_team: str
    away_team: str
    competition_name: str
    round_name_or_number: str | None
    kickoff: datetime
    status: MatchStatus
    home_score: int
    away_score: int
    minute: int | None = None
    added_time: int | None = None
    events: list[GoalEvent] = field(default_factory=list)
