from __future__ import annotations

from datetime import datetime
from zoneinfo import ZoneInfo

from .models import GoalEvent, Match


def minute_display(minute: int | None, added_time: int | None = None) -> str:
    if minute is None:
        return "?"
    if added_time:
        return f"{minute}+{added_time}'"
    return f"{minute}'"


def kickoff_london_text(kickoff: datetime, timezone: str) -> str:
    local = kickoff.astimezone(ZoneInfo(timezone))
    return local.strftime("%d-%m-%Y %H:%M")


def goal_line(goal: GoalEvent) -> str:
    flags = ""
    if goal.is_penalty:
        flags += " (Pen.)"
    if goal.is_own_goal:
        flags += " (OG)"
    minute = minute_display(goal.minute, goal.added_time)
    return f"• {minute} {goal.player_name}{flags} ({goal.team})"


def format_next_match(match: Match, timezone: str) -> str:
    lines = [
        f"🗓️ Next match: {match.home_team} vs {match.away_team}",
        f"🕒 Kickoff (London): {kickoff_london_text(match.kickoff, timezone)}",
    ]
    if match.round_name_or_number:
        lines.append(f"🏆 {match.competition_name} ({match.round_name_or_number})")
    else:
        lines.append(f"🏆 {match.competition_name}")
    lines.append("#UPTHETAGS")
    return "\n".join(lines)


def format_countdown(match: Match, timezone: str, remaining_minutes: int) -> str:
    return "\n".join(
        [
            f"⏳ Kickoff in {remaining_minutes}m: {match.home_team} vs {match.away_team}",
            f"🕒 Kickoff (London): {kickoff_london_text(match.kickoff, timezone)}",
            "#UPTHETAGS",
        ]
    )


def format_live(match: Match, new_goals: list[GoalEvent]) -> str:
    scoreline = (
        f"{match.home_team} {match.home_score} – "
        f"{match.away_score} {match.away_team}"
    )
    lines = [f"⚽ Live ({minute_display(match.minute, match.added_time)}): {scoreline}"]
    if new_goals:
        lines.append("⚽ Goals (new):")
        lines.extend(goal_line(g) for g in new_goals)
    lines.append("#UPTHETAGS")
    return "\n".join(lines)


def format_full_time(match: Match, timezone: str) -> str:
    lines = [
        f"✅ Full-time: {match.home_team} vs {match.away_team}",
        f"📊 Final score: {match.home_score} – {match.away_score}",
        f"🕒 Kickoff (London): {kickoff_london_text(match.kickoff, timezone)}",
    ]
    if match.round_name_or_number:
        lines.append(f"🏆 {match.competition_name} ({match.round_name_or_number})")
    else:
        lines.append(f"🏆 {match.competition_name}")
    if match.events:
        lines.append("⚽ Goals:")
        lines.extend(goal_line(g) for g in match.events)
    else:
        lines.append("⚽ Goals: No goals recorded.")
    lines.append("#UPTHETAGS")
    return "\n".join(lines)


def build_post_key(
    match: Match,
    countdown_bucket: int | None,
    last_goal_event_id: str | None,
) -> str:
    minute = minute_display(match.minute, match.added_time)
    phase = "pre" if match.minute is None else f"live:{minute}"
    bucket = f"bucket:{countdown_bucket}" if countdown_bucket is not None else "bucket:none"
    last_event = last_goal_event_id or "none"
    return (
        f"{phase}|{bucket}|{match.home_score}-{match.away_score}|"
        f"{last_event}|{match.status.value}"
    )
