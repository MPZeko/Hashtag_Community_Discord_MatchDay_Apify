# Hashtag Community Discord Matchday Bot (Apify)

Discord webhook bot for Hashtag United matchday updates, powered by an Apify actor and GitHub Actions schedules.

## Features
- No FotMob dependency (Apify only)
- Slow runner (2h) discovers next match and posts one-time next-match message in the 24h prematch window
- Fast runner (5m) no-ops outside fast window, then posts countdown/live updates with idempotent post keys
- One-time full-time recap with goals list, stoppage time, and Pen./OG markers
- Repo-committed JSON state for dedupe/idempotency

## Required secrets and variables
### Secrets
- `DISCORD_WEBHOOK_URL`
- `APIFY_API_TOKEN` (required unless token is embedded in `APIFY_ACTOR_ID`)

### Variables
- `APIFY_ACTOR_ID` (optional; defaults to `macheta~football-super-fast-data`)
- `APIFY_INPUT_JSON` (optional JSON object)
- `TEAM_NAME` (default `Hashtag United`)
- `TIMEZONE` (default `Europe/London`)
- `PREMATCH_WINDOW_HOURS` (default `24`)
- `FAST_WINDOW_BEFORE_MINUTES` (default `60`)
- `FAST_WINDOW_AFTER_MINUTES` (default `30`)
- `EXPECTED_MATCH_DURATION_MINUTES` (default `120`)
- `LOG_LEVEL` (default `INFO`)

## APIFY_ACTOR_ID supported formats
The bot accepts either separate token (`APIFY_API_TOKEN`) or embedded token in `APIFY_ACTOR_ID`.

Notes:
- Default actor id in code: `macheta~football-super-fast-data`.
- Set `APIFY_ACTOR_ID` only when you want to override the default actor.

Supported `APIFY_ACTOR_ID` formats:
- `macheta/football-super-fast-data`
- `macheta~football-super-fast-data`
- `macheta/football-super-fast-data?token=XXXX`
- `macheta~football-super-fast-data|XXXX`
- `macheta~football-super-fast-data token=XXXX`

Notes:
- Recommended: keep `APIFY_API_TOKEN` in **Secrets**.
- If you embed token in `APIFY_ACTOR_ID`, store `APIFY_ACTOR_ID` as a **Secret** (not Variable).
- If both are present, `APIFY_API_TOKEN` overrides embedded token.

## Local usage
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

DISCORD_WEBHOOK_URL=... \
APIFY_ACTOR_ID='macheta/football-super-fast-data?token=XXX' \
python -m matchday_bot.main --mode slow --dry-run --dump-raw

DISCORD_WEBHOOK_URL=... \
APIFY_ACTOR_ID='macheta/football-super-fast-data' \
APIFY_API_TOKEN='XXX' \
python -m matchday_bot.main --mode fast --dry-run
```

## Workflows
- `.github/workflows/matchday_slow.yml` — every 2 hours + manual dispatch
- `.github/workflows/matchday_fast.yml` — every 5 minutes + manual dispatch

Both workflows auto-commit state updates to `state/matchday_state.json`.


## LOG_LEVEL handling
- `LOG_LEVEL` accepts standard names (`DEBUG`, `INFO`, `WARNING`/`WARN`, `ERROR`, `CRITICAL`) or numeric levels (e.g. `20`).
- Missing, empty, or invalid values automatically fall back to `INFO` so runs do not fail.
