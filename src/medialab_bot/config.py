from pydantic_settings import BaseSettings, SettingsConfigDict


class AppConfig(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    discord_token: str
    discord_guild_id: int

    # The bot's single downstream dependency: the medialab-orchestrator gateway.
    # It no longer holds torrent-downloader/jellyfin URLs or keys, nor any
    # save-path config - placement and fan-out live behind the gateway.
    orchestrator_url: str
    orchestrator_api_key: str

    select_max_results: int = 25
    torrent_results_per_resolution: int = 5
    torrent_search_timeout_seconds: float = 30.0
    log_level: str = "INFO"
