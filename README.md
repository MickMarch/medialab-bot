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
| `/search <query>` | TMDB search (options marked `in Jellyfin` / `saved` / `following`), then title (shown with its poster) -> (season/episode scope for shows) -> torrent pick -> download. The only download path. | `GET /search/tmdb`, `GET /search/tmdb/{movie\|show}/{id}`, `GET /search/torrents`, `POST /download` |
| `/popular type:<movie\|show> [genre]` | Trending titles (top `SELECT_MAX_RESULTS`, `title (year) - rating`, marked `in Jellyfin` / `saved` / `following`), optionally narrowed to one genre (autocompleted). Pick one to see its poster and overview, then **Download** (same scope and torrent steps as `/search`), **Save** / **Unsave**, and for shows **Follow** / **Unfollow** (one tap: new episodes only at the default resolution; an unsaved show is saved first). Ephemeral. | `GET /discover/{movie\|show}`, `GET /discover/{movie\|show}/genres`, `PUT /watchlist/{movie\|show}/{id}`, `DELETE /watchlist/{movie\|show}/{id}`, `PUT /watchlist/show/{id}/follow`, `DELETE /watchlist/show/{id}/follow` |
| `/watchlist [kind:<saved\|following>]` | The shared watchlist (also edited from the web UI), optionally one kind. A followed show shows `following` and its last submitted episode. Pick a title for **Download**, **Unsave**, or (shows) **Follow** / **Unfollow**. Other follow controls (start point, pause, check now, episode view) are web only. Ephemeral. | `GET /watchlist`, `PUT /watchlist/{movie\|show}/{id}`, `DELETE /watchlist/{movie\|show}/{id}`, `PUT /watchlist/show/{id}/follow`, `DELETE /watchlist/show/{id}/follow` |
| `/transfers` | Live transfers merged with pipeline job rows. | `GET /transfers` |
| `/jobs [status]` | Pipeline lifecycle view; downloading jobs show a text progress bar with percent and ETA. Retry and Dismiss controls for `FAILED` and `NEEDS_ATTENTION` jobs; Dismiss closes a job without touching files. | `GET /jobs`, `POST /jobs/{id}/retry`, `POST /jobs/{id}/dismiss` |
| `/storage` | Disk usage. | `GET /storage` |
| `/delete` | Undo a download at any stage. Three steps: pick it (`Title (Year)`, then status, date and release name so copies differ), review the exact paths, press the red Delete button (60 s). Nothing is touched before that button. Ephemeral. | `GET /jobs`, `GET /jobs/{id}/deletion-plan`, `DELETE /jobs/{id}` |
| `/stop-seeding` | Pause every completed (seeding) torrent; downloads untouched. Ephemeral. | `POST /transfers/stop-seeding` |

All routes are under `/api/v1` on the orchestrator. Rate-limit `429`s carry
`Retry-After` and are surfaced to the user. Startup logs the gateway's
aggregated health (`GET /health`).

Deferred: `/similar` (awaits a TMDB passthrough on the gateway);
`/torrent` raw search without TMDB (tracked as
[MickMarch/medialab#26](https://github.com/MickMarch/medialab/issues/26)).

## Development

```bash
uv run pytest
uv run ruff check . && uv run ruff format --check . && uv run mypy src
```

Standards, workflow and release process: [workspace CLAUDE.md](../CLAUDE.md).
Code-local notes: [CLAUDE.md](CLAUDE.md).
