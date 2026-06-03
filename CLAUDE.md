# CLAUDE.md - medialab-bot

Discord bot that provides slash command UI for the torrent-downloader service.
Independent git repo inside the `medialab/` workspace.

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
- `TORRENT_DOWNLOADER_URL` - Base URL of torrent-downloader (e.g. `http://127.0.0.1:8000`)
- `TORRENT_DOWNLOADER_API_KEY` - Value for `X-API-Key` header sent to torrent-downloader

Optional (defaults shown):
- `LOG_LEVEL=INFO`

## Architecture

Thin UI layer. No business logic - delegates all work to torrent-downloader over HTTP.

```
Discord user
    | slash command
medialab-bot (discord.py)
    | HTTP + X-API-Key header
torrent-downloader (FastAPI, port 8000)
    |
qBittorrent + TMDB
```

**Tech stack:** `discord.py`, `uv`, `hatchling + hatch-vcs`, `pydantic-settings`, `httpx`

**Multi-step download flow:**
1. User calls `/search <query> [type]`
   - Always calls `GET /api/v1/search/tmdb?query=...` first to get TMDB IDs and a result list
   - If `type` provided: immediately fetches type-specific detail for each result via `/search/tmdb/movie/{id}` or `/search/tmdb/show/{id}` - richer metadata
   - If no `type`: presents multi-search results as-is
   - Bot presents results as Discord embed with Select menu
2. User picks title - bot calls `GET /api/v1/search/torrents`, presents resolution options as Select menu
3. User picks torrent - bot calls `POST /api/v1/download` with the selected magnet URI
4. State lives entirely in Discord message components - no server-side session

**All Discord interaction state is stored in the message components themselves** (custom_id encodes what the next step is). No database, no in-memory session dict needed.

**Response models:** `client.py` deserializes all torrent-downloader responses into Pydantic models defined in `schemas/`. Cogs receive typed objects, never raw dicts. `main.py` stays thin - bot init, cog loading, startup health check only.

## torrent-downloader API contract

Base URL from `TORRENT_DOWNLOADER_URL`. All requests (except health) send `X-API-Key: <TORRENT_DOWNLOADER_API_KEY>` header.

| Endpoint | Method | Bot uses it for |
|---|---|---|
| `/api/v1/health` | GET | Startup connectivity check |
| `/api/v1/search/tmdb` | GET | `/search` command - params: `query`, `type` (movie/tv) |
| `/api/v1/search/tmdb/movie/{tmdb_id}` | GET | Fetch movie detail after user selects result |
| `/api/v1/search/tmdb/show/{tmdb_id}` | GET | Fetch show detail after user selects result |
| `/api/v1/search/torrents` | GET | Torrent picker - params: `query` |
| `/api/v1/download` | POST | Submit confirmed magnet URI |
| `/api/v1/transfers` | GET | `/transfers` command |
| `/api/v1/storage` | GET | `/storage` command |

Error shape from torrent-downloader: `{"status": "error", "code": "<ErrorCode>", "detail": "..."}`.
Rate limit breach returns 429 with `Retry-After` header - bot should surface this to the user.

v1.1 endpoints (not yet available - skip these commands until torrent-downloader ships v1.1):
- `GET /api/v1/search/trending?type=movie|show&window=day|week` - for `/trending`
- `GET /api/v1/search/similar?tmdb_id=123&type=movie|show` - for `/similar`

## Slash commands

| Command | Status | Description |
|---|---|---|
| `/search <query> <type>` | planned | TMDB search, embed + select menu |
| `/torrent <query>` | planned | Skip TMDB, go straight to torrent search |
| `/download` | planned | Confirm and submit selected magnet |
| `/transfers` | planned | List active downloads |
| `/storage` | planned | Disk usage |
| `/trending <type>` | blocked on v1.1 | Trending movies or shows |
| `/similar <title> <type>` | blocked on v1.1 | Similar titles |

## Module layout (target structure)

```
src/medialab_bot/
├── __init__.py
├── main.py          - bot entrypoint, registers cogs, startup health check, connects
├── config.py        - AppConfig pydantic-settings instance
├── client.py        - httpx AsyncClient wrapper; deserializes responses into schemas/
├── schemas/
│   ├── tmdb.py      - TmdbMultiResult, TmdbMovieDetail, TmdbShowDetail
│   ├── torrents.py  - TorrentSearchResult, grouped by resolution
│   ├── transfers.py - Transfer, TransferList
│   ├── storage.py   - StorageInfo
│   └── errors.py    - ErrorResponse (mirrors torrent-downloader error shape)
├── cogs/
│   ├── search.py    - /search, /torrent commands
│   ├── download.py  - /download command + component callbacks
│   ├── status.py    - /transfers, /storage commands
│   └── trending.py  - /trending, /similar (v1.1, not yet implemented)
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
