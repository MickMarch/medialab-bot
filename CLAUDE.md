# CLAUDE.md - medialab-bot

Discord bot providing the slash-command UI for the medialab suite. It talks to
exactly one service - the medialab-orchestrator gateway - which fronts the whole
media lifecycle. Independent git repo inside the `medialab/` workspace.

---

## Commands

```bash
# Install dependencies
uv sync --dev

# Run bot
uv run medialab-bot

# Run tests
uv run pytest

# Run single test
uv run pytest tests/test_commands.py::TestSearchCommand::test_search_returns_embed
```

## Environment Setup

Copy `.env.example` to `.env` and populate. Config loads via `pydantic-settings` from `.env`.

Required:
- `DISCORD_TOKEN` - Discord bot token
- `DISCORD_GUILD_ID` - Guild (server) ID to register slash commands against
- `ORCHESTRATOR_URL` - Base URL of medialab-orchestrator (e.g. `http://127.0.0.1:8000`)
- `ORCHESTRATOR_API_KEY` - Value for `X-API-Key` header sent to the orchestrator

Optional (defaults shown):
- `SELECT_MAX_RESULTS=25`, `TORRENT_RESULTS_PER_RESOLUTION=5`
- `TORRENT_SEARCH_TIMEOUT_SECONDS=30.0`, `LOG_LEVEL=INFO`

## Architecture

Thin UI layer. No business logic - the bot talks to exactly one service, the
medialab-orchestrator gateway, which fronts the whole lifecycle and fans out to
the downstream workers. The bot holds one URL + one key and no placement config.

```
Discord user
    | slash command
medialab-bot (discord.py)
    | HTTP + X-API-Key header
medialab-orchestrator (gateway) --> torrent-downloader (qBittorrent + TMDB)
                                \--> medialab-jellyfin (Jellyfin)
```

**Tech stack:** `discord.py`, `uv`, `hatchling + hatch-vcs`, `pydantic-settings`,
`httpx`, `medialab-contracts` (shared `MediaType`, `ErrorResponse`, `TransferInfo`).

**Multi-step download flow (the only download path):**
1. User calls `/search <query>` - bot calls `GET /api/v1/search/tmdb`, presents
   results as an embed + Select menu. Each option carries `tmdb_id` + media type.
2. User picks a title. For a **movie**, the bot calls `GET /api/v1/search/torrents`
   directly and presents resolution options. For a **show**, the bot first fetches
   the season list (`GET /api/v1/search/tmdb/show/{id}`) and presents a scope
   picker (whole series / a season / a single episode); the chosen
   `season`/`episode` are passed to the torrent search so the results target the
   requested season. **The picked `tmdb_id` + `media_type` are threaded into the
   torrent picker** (the gateway requires both at download; it does no title
   guessing).
3. User picks a torrent - bot calls `POST /api/v1/download` with
   `{magnet_uri, media_type, tmdb_id}`. The gateway creates a pipeline job and
   returns it; the bot shows the job hash so the user can `/jobs` it.
4. State lives entirely in Discord message components - no server-side session.

TMDB classifies titles `movie`/`tv`; the suite uses `movie`/`show`
(`medialab_bot.media.from_tmdb_media_type` maps at the boundary).

**Response models:** the client deserializes all gateway responses into Pydantic
models in `schemas/` (shared shapes re-exported from `medialab-contracts`). Cogs
receive typed objects, never raw dicts. `main.py` stays thin - bot init, cog
loading, aggregated startup health.

## medialab-orchestrator API contract

Base URL from `ORCHESTRATOR_URL`. All requests (except health) send
`X-API-Key: <ORCHESTRATOR_API_KEY>`.

| Endpoint | Method | Bot uses it for |
|---|---|---|
| `/api/v1/health` | GET | Startup check; aggregated downstream reachability |
| `/api/v1/search/tmdb` | GET | `/search` - param: `query` |
| `/api/v1/search/tmdb/{movie,show}/{tmdb_id}` | GET | Detail after a result pick |
| `/api/v1/search/torrents` | GET | Torrent picker - params: `query`, `media_type` (required); shows add optional `season`/`episode` |
| `/api/v1/download` | POST | Submit `{magnet_uri, media_type, tmdb_id}`; returns a job (202) |
| `/api/v1/transfers` | GET | `/transfers` - merged live transfers + job rows |
| `/api/v1/jobs` | GET | `/jobs` - pipeline lifecycle; optional `status` filter |
| `/api/v1/jobs/{hash}/retry` | POST | Retry a failed job from its last good state |
| `/api/v1/storage` | GET | `/storage` - no path param |

Error shape: `{"status": "error", "code": "<ErrorCode>", "detail": "..."}`.
Rate-limit breach returns 429 with `Retry-After` - surface it to the user.

`/trending` + `/similar` remain deferred (await torrent-downloader's TMDB
roadmap, surfaced through the gateway when it ships).

## Slash commands

| Command | Status | Description |
|---|---|---|
| `/search <query>` | live | TMDB search; sole download path (threads tmdb_id+media_type) |
| `/transfers` | live | Active transfers merged with pipeline jobs |
| `/storage` | live | Disk usage |
| `/jobs [status]` | live | Pipeline lifecycle view; retry control for failed jobs |
| `/trending <type>` | deferred | Awaits gateway TMDB-trending passthrough |
| `/similar <title> <type>` | deferred | Awaits gateway TMDB-similar passthrough |

`/torrent` was removed: it cannot supply the `tmdb_id` + `media_type` the gateway
requires, so downloads go through `/search`.

## Module layout

```
src/medialab_bot/
├── __init__.py
├── main.py          - bot entrypoint, cog registration, aggregated startup health
├── config.py        - AppConfig pydantic-settings instance
├── media.py         - TMDB media-type (movie/tv) -> contracts MediaType (movie/show)
├── client/          - OrchestratorClient: httpx wrapper as mixins, parses into schemas/
│   ├── __init__.py  - OrchestratorClient (composes the mixins)
│   ├── _base.py     - shared GET/POST + parse helpers
│   ├── _tmdb.py     - search proxies
│   ├── _torrents.py - torrent search + download (media_type + tmdb_id)
│   ├── _status.py   - health, transfers, storage
│   └── _jobs.py     - list_jobs, retry_job
├── schemas/
│   ├── tmdb.py      - TMDB search/detail models
│   ├── torrents.py  - torrent results grouped by resolution
│   ├── transfers.py - MergedTransfersResponse (live transfers + job rows)
│   ├── jobs.py      - JobView, JobsResponse
│   ├── system.py    - aggregated HealthResponse, DiskUsageResponse
│   ├── downloads.py - DownloadResponse (wraps a JobView)
│   └── errors.py    - re-export of contracts ErrorResponse
├── cogs/
│   ├── search.py    - /search command
│   ├── status.py    - /transfers, /storage commands
│   └── jobs.py      - /jobs command (+ retry view)
├── views/
│   ├── tmdb.py      - TmdbSelectMenu (movie -> torrent search; show -> scope picker)
│   ├── scope.py     - SeasonScopeSelectMenu + EpisodeScopeSelectMenu (TV targeting)
│   ├── torrent.py   - TorrentSelectMenu (submits download) + run_torrent_search helper
│   └── jobs.py      - JobRetryView
└── embeds.py        - Discord embed builders (keeps cogs thin)

tests/
├── conftest.py      - shared fixtures (mock client, mock interactions)
├── test_client.py   - client.py unit tests (mock httpx)
├── test_schemas.py  - Pydantic model parsing/validation
├── test_embeds.py   - embed builder output
├── cogs/
│   ├── test_search.py
│   ├── test_download.py
│   ├── test_status.py
│   └── test_trending.py
└── integration/     - skipped without live credentials (mark with pytest.mark.integration)
```

## Versioning

Version derived from git tags via `hatch-vcs` - never hardcode it.
`src/medialab_bot/_version.py` is generated at build time and is gitignored.

Release process: merge to main, tag (`git tag -a vX.Y.Z -m "vX.Y.Z"`), push tag, create GitHub Release, update `CHANGELOG.md` before tagging.

## Development workflow

**Spec-first, test-driven. No exceptions.**

1. Write a spec (inputs, outputs, behavior, edge cases) and get explicit approval
2. Write failing tests that encode the spec
3. Implement until tests pass

Never write implementation code before a spec is approved. Never skip failing tests and go straight to code.

## Shared conventions

- Python 3.12+
- Package manager: `uv` (not pip, not poetry)
- Build backend: `hatchling + hatch-vcs`
- Tests: `pytest` style only, run via `uv run pytest`
- Commits: Conventional Commits (`feat`, `fix`, `chore`, etc.)
- Workflow: spec approval → failing tests → implementation (never skip to code)
- No hardcoded secrets - `.env` for local dev, gitignored always
- No em dash character anywhere
- No AI attribution in commit messages or code comments (exception: CLAUDE.md and .claude/)
- Branch strategy: feature branches off main, PR to merge

## Testing patterns

- `uv run pytest` always, never `python -m pytest`
- pytest style always, never unittest
- Mock `httpx.AsyncClient` calls to torrent-downloader - do not require a live service for unit tests
- Test Discord interactions by constructing `discord.Interaction` mocks
- Integration tests (if added) should be clearly separated and skippable without a live bot token
