from datetime import datetime, timezone

from matchday_bot.formatting import build_post_key, goal_line, minute_display
from matchday_bot.models import GoalEvent, Match, MatchStatus


def _match() -> Match:
    return Match(
        match_id="m1",
        home_team="Hashtag United",
        away_team="Opponent FC",
        competition_name="League",
        round_name_or_number="31",
        kickoff=datetime(2026, 1, 1, 12, 0, tzinfo=timezone.utc),
        status=MatchStatus.LIVE,
        home_score=1,
        away_score=0,
        minute=45,
        added_time=4,
    )


def test_minute_display_stoppage() -> None:
    assert minute_display(45, 4) == "45+4'"


def test_goal_line_penalty_own_goal_suffix() -> None:
    event = GoalEvent("1", "Hashtag United", "Player A", 90, 2, True, True)
    assert goal_line(event) == "• 90+2' Player A (Pen.) (OG) (Hashtag United)"


def test_post_key_changes_with_event() -> None:
    match = _match()
    key1 = build_post_key(match, None, "e1")
    key2 = build_post_key(match, None, "e2")
    assert key1 != key2
