# CLAUDE.md - medialab-bot

Workspace rules, conventions, standards and workflow live in the root
[`medialab/CLAUDE.md`](../CLAUDE.md); it is the authority when anything here
disagrees. This file holds only what is specific to this code.

## Commands

```bash
uv sync --dev
uv run medialab-bot
uv run pytest
uv run pytest tests/cogs/test_search.py::test_torrent_select_options_sorted_descending_by_seeders
```

## Config

`.env.example` is the authoritative variable list; `config.py` holds the
defaults. The bot has exactly one downstream: `ORCHESTRATOR_URL` +
`ORCHESTRATOR_API_KEY`. No placement or save-path config belongs here.

## Architecture

Thin UI layer over the medialab-orchestrator gateway. No business logic, no
server-side session: multi-step state lives in Discord message components.
Commands and the gateway routes they use: [README](README.md).

**Download flow (the only one):**
1. `/search <query>` -> `GET /search/tmdb`, embed + Select. Each option
   carries `tmdb_id` + media type.
2. Pick a title. Movie -> `GET /search/torrents` directly. Show -> fetch the
   season list (`GET /search/tmdb/show/{id}`), present the scope picker
   (whole series / season / episode), pass `season`/`episode` into the
   torrent search.
3. Pick a torrent -> `POST /download` with `{source_url, media_type, tmdb_id}`.
   The gateway requires all three and does no title guessing. The returned
   job id is shown so the user can `/jobs` it.

TMDB says `movie`/`tv`; the suite says `movie`/`show`. `media.from_tmdb_media_type`
maps at that boundary.

The client (`client/`) deserializes every gateway response into Pydantic
models in `schemas/` (shared shapes re-exported from `medialab-contracts`).
Cogs receive typed objects, never dicts. `main.py` stays thin: bot init, cog
loading, aggregated startup health.

## Module layout

```
src/medialab_bot/
├── main.py        entrypoint, cog registration, startup health log
├── config.py      AppConfig (pydantic-settings)
├── constants.py   Discord limits and other named values
├── startup.py     bounded retry with backoff around the Discord login
├── media.py       TMDB media type -> contracts MediaType
├── client/        OrchestratorClient as mixins: _base (GET/POST/parse), _tmdb,
│                  _torrents (search + download), _status (health/transfers/storage), _jobs
├── schemas/       tmdb, torrents, transfers, jobs, system, downloads, errors
├── cogs/          search (/search), status (/transfers, /storage), jobs (/jobs)
├── views/         tmdb (TmdbSelectMenu), scope (season/episode pickers),
│                  torrent (TorrentSelectMenu + run_torrent_search), jobs (JobRetryView)
└── embeds.py      embed builders

tests/
├── conftest.py    mock client + mock interactions
├── helpers.py
├── test_client.py test_schemas.py test_embeds.py test_media.py
└── cogs/          test_search, test_scope, test_status, test_jobs
```

## Testing patterns

- Mock `OrchestratorClient` (the class) in cog tests, never `httpx`. Only
  `test_client.py` mocks `httpx.AsyncClient`.
- Test Discord interactions by constructing `discord.Interaction` mocks
  (`tests/conftest.py`).
- The torrent search pattern is `Title YYYY`, never `Title (YYYY)`;
  parentheses appear only in display strings. Keep that when touching
  `run_torrent_search`.
