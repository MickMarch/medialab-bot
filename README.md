# medialab-bot

Discord slash-command UI for the [medialab](https://github.com/MickMarch/medialab)
suite. A thin UI layer: it talks to exactly one service, the
medialab-orchestrator gateway, and holds no business logic or server-side
state.

```
Discord user
    | slash command
medialab-bot (discord.py)
    | HTTP + X-API-Key
medialab-orchestrator (gateway) --> torrent-downloader, medialab-jellyfin
```

## Setup

Prerequisites: Python 3.12+, [uv](https://docs.astral.sh/uv/), a running
orchestrator, and a bot token from the
[Discord Developer Portal](https://discord.com/developers/applications).

```bash
uv sync --dev
cp .env.example .env     # then fill in the values
uv run medialab-bot
```

`.env.example` documents every variable. The bot needs the token, the guild
id to register commands against, and the orchestrator URL + key.

Invite the bot with OAuth2 scopes `bot` + `applications.commands` and
permissions `Send Messages`, `Embed Links`.

The bot runs as a container from the workspace `docker-compose.yml`; see the
[workspace README](../README.md).

## Commands

| Command | Description | Gateway routes used |
|---|---|---|
| `/search <query>` | TMDB search, then title -> (season/episode scope for shows) -> torrent pick -> download. The only download path. | `GET /search/tmdb`, `GET /search/tmdb/{movie\|show}/{id}`, `GET /search/torrents`, `POST /download` |
| `/transfers` | Live transfers merged with pipeline job rows. | `GET /transfers` |
| `/jobs [status]` | Pipeline lifecycle view with a retry control for `FAILED` and `NEEDS_ATTENTION` jobs. | `GET /jobs`, `POST /jobs/{id}/retry` |
| `/storage` | Disk usage. | `GET /storage` |
| `/delete` | Undo a download at any stage. Three steps: pick it (`Title (Year)`, then status, date and release name so copies differ), review the exact paths, press the red Delete button (60 s). Nothing is touched before that button. Ephemeral. | `GET /jobs`, `GET /jobs/{id}/deletion-plan`, `DELETE /jobs/{id}` |
| `/stop-seeding` | Pause every completed (seeding) torrent; downloads untouched. Ephemeral. | `POST /transfers/stop-seeding` |

All routes are under `/api/v1` on the orchestrator. Rate-limit `429`s carry
`Retry-After` and are surfaced to the user. Startup logs the gateway's
aggregated health (`GET /health`).

Deferred: `/trending` and `/similar` (await TMDB passthroughs on the gateway);
`/torrent` raw search without TMDB (tracked as
[MickMarch/medialab#26](https://github.com/MickMarch/medialab/issues/26)).

## Development

```bash
uv run pytest
uv run ruff check . && uv run ruff format --check . && uv run mypy src
```

Standards, workflow and release process: [workspace CLAUDE.md](../CLAUDE.md).
Code-local notes: [CLAUDE.md](CLAUDE.md).
