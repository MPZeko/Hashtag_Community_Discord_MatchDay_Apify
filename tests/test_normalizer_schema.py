from matchday_bot.normalizer import choose_next_match, normalize_match


def test_normalize_match_supports_utc_date_and_team_objects() -> None:
    raw = {
        "id": "abc",
        "utcDate": "2026-03-01T15:00:00Z",
        "homeTeam": {"name": "Hashtag United"},
        "awayTeam": {"name": "Rivals FC"},
        "status": "scheduled",
        "homeScore": 0,
        "awayScore": 0,
    }

    match = normalize_match(raw)

    assert match.match_id == "abc"
    assert match.home_team == "Hashtag United"
    assert match.away_team == "Rivals FC"


def test_choose_next_match_supports_nested_payload_shape() -> None:
    items = [
        {
            "data": {
                "fixtures": [
                    {
                        "eventId": "1",
                        "matchDate": "2026-03-01 15:00:00",
                        "home": {"name": "Hashtag United"},
                        "away": {"name": "Opponent FC"},
                    }
                ]
            }
        }
    ]

    match = choose_next_match(items, "Hashtag United")

    assert match.match_id == "1"
    assert match.home_team == "Hashtag United"
    assert match.away_team == "Opponent FC"
