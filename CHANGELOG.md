# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Fixed

- Show torrent searches no longer append the series' premiere year to the
  query. Release names do not include it, so "The Wire 2002" returned zero
  hits for every scope. Shows now search on the bare title; movies keep
  `Title YYYY`.

## [2.1.0] - 2026-07-02

### Added

- TV season/episode scope picker. After picking a show, the bot fetches the
  season list from `GET /search/tmdb/show/{id}` and presents a scope Select
  (whole series / a season / a single episode). Picking a season opens an
  episode Select (whole season / a specific episode). The chosen scope is
  threaded into `GET /search/torrents` so older seasons are no longer buried by
  the latest season's higher-seeded packs. Movies are unaffected - they skip
  straight to the torrent picker.
- `run_torrent_search` shared helper (`views/torrent.py`) driving the scoped
  search + torrent picker for both the movie path and the TV scope pickers.

### Changed

- `OrchestratorClient.search_torrents` now takes a required `media_type` and
  optional `season`/`episode`.
- `medialab-contracts` pin bumped to v0.3.0.

## [2.0.0] - 2026-06-29

Breaking: the bot is rewired onto the medialab-orchestrator gateway as its sole
dependency. The client surface, config fields, and command set changed
incompatibly with v1.0.0 (which talked directly to torrent-downloader).

### Fixed

- `/jobs` crashed with `TypeError: expected view parameter to be of type View ...
  not NoneType` when no job in the result set was failed. The cog now omits the
  `view` kwarg entirely rather than passing `view=None` (which discord.py
  rejects). Regression-guarded by a test that mirrors discord.py's contract.

### Added

- Dockerfile + `.dockerignore`: two-stage uv install with git for the
  `medialab-contracts` git-ref dependency, non-root user, no `EXPOSE`
  (outbound-only client). Enables the bot in the root `docker-compose.yml`.
- `/jobs [status]` command surfacing the orchestrator's pipeline lifecycle, with
  a retry control for failed jobs (`POST /jobs/{hash}/retry`).
- `medialab-contracts` dependency (pinned `v0.2.0`); `MediaType`, `ErrorResponse`,
  and `TransferInfo` now come from the shared package instead of local copies.
- `media.py` mapping TMDB's `movie`/`tv` media types onto the shared
  `MediaType` (`movie`/`show`).
- Ruff lint + format configuration enforcing the workspace rule set
  (`E,F,I,UP,B,SIM,PLR2004`, magic-value ban via `PLR2004`).
- Mypy static type checking with the pydantic plugin; discord.py
  interaction/view typing artifacts relaxed per-module (not behavior bugs).
- Pre-commit hooks (ruff, whitespace, eof, yaml/toml checks).
- Dependabot config for `uv` and GitHub Actions updates.
- GitHub Actions CI workflow (the first for this service): ruff lint, format
  check, mypy, tests, and a project-dependency audit.

### Changed

- **Rewired the bot onto the medialab-orchestrator gateway as its single
  dependency.** All calls now target the orchestrator; the client is renamed
  `OrchestratorClient`. Download submits `{magnet_uri, media_type, tmdb_id}` and
  receives a pipeline job; `/transfers` renders the gateway's merged
  transfers+jobs view; `/storage` no longer sends a path; startup health uses
  the orchestrator's aggregated downstream-reachability signal.
- The TMDB pick now threads `tmdb_id` + `media_type` through to the download
  call (previously only the title string flowed on), as the gateway requires
  both and does no title guessing.
- Bumped `aiohttp` (>=3.14.1) and `pydantic-settings` (>=2.14.2) to clear CVEs
  surfaced by the new dependency audit.
- Replaced a magic `200` status comparison with `httpx.codes.OK`.

### Removed

- The `/torrent` direct-search command (and its cog): it cannot supply the
  `tmdb_id` + `media_type` the gateway requires, so `/search` is the sole
  download path. The torrent resolution-picker view is retained for the
  `/search` flow.
- Bot tech-debt config (`torrent_downloader_url`/`_api_key`,
  `torrent_save_path`, `tmp_docker_save_path`), replaced by `orchestrator_url`
  and `orchestrator_api_key`. Placement and downstream fan-out live behind the
  gateway now.

## [1.0.0] - 2026-06-08

### Added

- `/torrent <query>` slash command - skips TMDB, searches torrents directly and presents resolution picker
- `/transfers` slash command - lists active downloads with progress, state, and speed
- `/storage` slash command - shows disk usage for the configured path
- `TorrentSelectMenu` and `TmdbSelectMenu` views extracted to `views/` module, wiring full search-to-download flow
- `DiskUsageResponse`, `TransferInfoResponse`, `TorrentSearchResponse`, `DownloadResponse`, `ErrorResponse`, `TmdbMediaDetailResponse` schemas
- `_BaseClient`, `_TmdbMixin`, `_TorrentsMixin`, `_StatusMixin` - client split into domain mixins for maintainability
- `AppConfig` settings: `torrent_save_path`, `tmp_docker_save_path`, `select_max_results`, `torrent_results_per_resolution`, `torrent_search_timeout_seconds`
- `TMP_DOCKER_SAVE_PATH` env var - the bot and torrent-downloader run in separate containers without a shared filesystem, so `/storage` queries the docker-visible mount path rather than the host path
- 81 unit tests covering client, schemas, embeds, views, and cogs

### Changed

- Collapsed nested `StorageResponse`/`DiskUsage` into flat `DiskUsageResponse` matching the actual API shape
- `TorrentResult` fields renamed to snake_case (`file_name`, `seeders`, etc.) with Pydantic aliases for the camelCase API response; `seeders`/`leechers` constrained to non-negative
- `_parse` made generic so client methods return correctly-typed models
- All slash command responses now ephemeral; `/search` and `/torrent` show a progress message that is edited in place as results arrive

### Fixed

- Interaction flow hardened against expired tokens and double-acknowledgement during multi-step select flows
- Torrent search timeout configurable and enforced via `_torrent_search_timeout`

## [0.1.0] - 2026-06-04

### Added

- `/search <query>` slash command - searches TMDB, returns embed with results and a select menu
- `TorrentDownloaderClient` - httpx wrapper with constructor-injected URL and API key
- `AppConfig` via `pydantic-settings`, loaded from `.env`
- Startup health check against torrent-downloader; warns if unreachable or VPN not bound
- Guild-scoped slash command sync on bot ready via `setup_hook`
- `HealthResponse`, `TmdbSearchResult`, `TmdbSearchResponse` Pydantic schemas
- 25 unit tests covering client, schemas, embeds, and cog behavior

### Fixed

- Hardened client against `JSONDecodeError` and `ValidationError` on malformed API responses
- `/search` defers interaction before API call to avoid Discord 3-second timeout
- Select menu callback guards against malformed `interaction.data`

[Unreleased]: https://github.com/MickMarch/medialab-bot/compare/v1.0.0...HEAD
[1.0.0]: https://github.com/MickMarch/medialab-bot/compare/v0.1.0...v1.0.0
[0.1.0]: https://github.com/MickMarch/medialab-bot/releases/tag/v0.1.0
