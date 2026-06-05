from pydantic_settings import BaseSettings, SettingsConfigDict


class AppConfig(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    discord_token: str
    discord_guild_id: int
    torrent_downloader_url: str
    torrent_downloader_api_key: str
    torrent_save_path: str
    log_level: str = "INFO"
