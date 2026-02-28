from datetime import datetime, timedelta, timezone

from matchday_bot.main import in_fast_window
from matchday_bot.state_store import MatchdayState


def test_fast_window_no_op_outside() -> None:
    kickoff = datetime(2026, 1, 1, 12, 0, tzinfo=timezone.utc)
    now = kickoff - timedelta(minutes=120)
    assert not in_fast_window(now, kickoff, 60, 120, 30)


def test_fast_window_inside() -> None:
    kickoff = datetime(2026, 1, 1, 12, 0, tzinfo=timezone.utc)
    now = kickoff + timedelta(minutes=15)
    assert in_fast_window(now, kickoff, 60, 120, 30)


def test_state_idempotency_storage() -> None:
    state = MatchdayState()
    state.last_fast_post_key_by_match_id["abc"] = "k1"
    assert state.last_fast_post_key_by_match_id["abc"] == "k1"
