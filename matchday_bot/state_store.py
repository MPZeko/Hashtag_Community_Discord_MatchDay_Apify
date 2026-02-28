from __future__ import annotations

import json
import logging
from dataclasses import asdict, dataclass, field
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class MatchdayState:
    next_match_id: str = ""
    next_match_kickoff_iso: str = ""
    posted_next_match_for_match_id: str | None = None
    posted_full_time_for_match_id: str | None = None
    last_fast_post_key_by_match_id: dict[str, str] = field(default_factory=dict)
    last_seen_event_ids_by_match_id: dict[str, list[str]] = field(default_factory=dict)


class StateStore:
    def __init__(self, path: str = "state/matchday_state.json") -> None:
        self.path = Path(path)

    def load(self) -> MatchdayState:
        if not self.path.exists():
            logger.warning("state file missing, using default")
            return MatchdayState()
        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))
            return MatchdayState(**data)
        except Exception:
            logger.warning("state file corrupt, resetting", exc_info=True)
            return MatchdayState()

    def save(self, state: MatchdayState) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        tmp = self.path.with_suffix(".tmp")
        tmp.write_text(json.dumps(asdict(state), indent=2, sort_keys=True), encoding="utf-8")
        tmp.replace(self.path)
