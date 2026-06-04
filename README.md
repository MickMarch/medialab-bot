# medialab-bot

Discord bot providing slash command UI for the [torrent-downloader](https://github.com/MickMarch/torrent-downloader) service.

Part of the `medialab` workspace. Thin UI layer - no business logic lives here.

## Architecture

```
Discord user
    | slash command
medialab-bot (discord.py)
    | HTTP + X-API-Key header
torrent-downloader (FastAPI)
    |
qBittorrent + TMDB
```

## Setup

### Prerequisites

- Python 3.12+
- [uv](https://docs.astral.sh/uv/)
- A running [torrent-downloader](https://github.com/MickMarch/torrent-downloader) instance
- A Discord bot token ([Discord Developer Portal](https://discord.com/developers/applications))

### Installation

```bash
uv sync --dev
```

### Configuration

Copy `.env.example` to `.env` and populate all values:

```bash
cp .env.example .env
```

| Variable | Required | Description |
|---|---|---|
| `DISCORD_TOKEN` | Yes | Discord bot token |
| `DISCORD_GUILD_ID` | Yes | Guild (server) ID for slash command registration |
| `TORRENT_DOWNLOADER_URL` | Yes | Base URL of torrent-downloader (e.g. `http://127.0.0.1:8000`) |
| `TORRENT_DOWNLOADER_API_KEY` | Yes | `X-API-Key` header value for torrent-downloader |
| `LOG_LEVEL` | No | Log level (default: `INFO`) |

### Discord Bot Permissions

When inviting the bot, use OAuth2 scopes `bot` + `applications.commands` with permissions: `Send Messages`, `Embed Links`.

### Running

```bash
uv run medialab-bot
```

## Commands

| Command | Status | Description |
|---|---|---|
| `/search <query>` | Available | Search TMDB, pick a title via select menu |
| `/torrent <query>` | Planned | Skip TMDB, search torrents directly |
| `/download` | Planned | Confirm and submit selected magnet URI |
| `/transfers` | Planned | List active downloads |
| `/storage` | Planned | Disk usage |
| `/trending <type>` | Blocked on torrent-downloader v1.1 | Trending movies or shows |
| `/similar <title> <type>` | Blocked on torrent-downloader v1.1 | Similar titles |

## Development

```bash
# Run tests
uv run pytest

# Run single test
uv run pytest tests/test_client.py::test_health_returns_response_on_200
```

See [CLAUDE.md](CLAUDE.md) for architecture decisions, module layout, and development workflow.

## Versioning

Version derived from git tags via `hatch-vcs`. Never hardcoded.

Release process: merge to main → tag (`git tag -a vX.Y.Z -m "vX.Y.Z"`) → push tag → create GitHub Release → update `CHANGELOG.md`.
