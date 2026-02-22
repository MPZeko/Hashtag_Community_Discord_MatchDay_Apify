import pytest

from matchday_bot.config import load_settings, parse_apify_actor_ref


@pytest.mark.parametrize(
    ("raw", "expected_actor", "expected_token"),
    [
        ("macheta/football-super-fast-data", "macheta~football-super-fast-data", None),
        ("macheta~football-super-fast-data", "macheta~football-super-fast-data", None),
        (
            "macheta/football-super-fast-data?token=abc",
            "macheta~football-super-fast-data",
            "abc",
        ),
        ("macheta~football-super-fast-data|abc", "macheta~football-super-fast-data", "abc"),
        (
            "macheta~football-super-fast-data token=abc",
            "macheta~football-super-fast-data",
            "abc",
        ),
    ],
)
def test_parse_apify_actor_ref(raw: str, expected_actor: str, expected_token: str | None) -> None:
    actor, token = parse_apify_actor_ref(raw)
    assert actor == expected_actor
    assert token == expected_token


def test_load_settings_env_token_override(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DISCORD_WEBHOOK_URL", "https://discord.test")
    monkeypatch.setenv("APIFY_ACTOR_ID", "macheta~football-super-fast-data?token=abc")
    monkeypatch.setenv("APIFY_API_TOKEN", "def")

    settings = load_settings()

    assert settings.apify_actor_id == "macheta~football-super-fast-data"
    assert settings.apify_api_token == "def"


def test_load_settings_embedded_token(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DISCORD_WEBHOOK_URL", "https://discord.test")
    monkeypatch.setenv("APIFY_ACTOR_ID", "macheta~football-super-fast-data|abc")
    monkeypatch.delenv("APIFY_API_TOKEN", raising=False)

    settings = load_settings()

    assert settings.apify_api_token == "abc"


def test_load_settings_missing_token_message(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DISCORD_WEBHOOK_URL", "https://discord.test")
    monkeypatch.setenv("APIFY_ACTOR_ID", "macheta~football-super-fast-data")
    monkeypatch.delenv("APIFY_API_TOKEN", raising=False)

    with pytest.raises(ValueError, match="Missing Apify API token"):
        load_settings()
