# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

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

[Unreleased]: https://github.com/MickMarch/medialab-bot/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/MickMarch/medialab-bot/releases/tag/v0.1.0
