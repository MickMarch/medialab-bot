import asyncio
import logging

import discord
from discord.ext import commands

from medialab_bot.client import TorrentDownloaderClient
from medialab_bot.config import AppConfig


async def _run(config: AppConfig) -> None:
    logging.basicConfig(level=config.log_level.upper())
    logger = logging.getLogger(__name__)

    client = TorrentDownloaderClient(
        base_url=config.torrent_downloader_url,
        api_key=config.torrent_downloader_api_key,
    )

    health = await client.health()
    if health is None:
        logger.warning("torrent-downloader unreachable at startup")
    elif not health.vpn_interface_bound:
        logger.warning("torrent-downloader reachable but VPN interface not bound")
    else:
        logger.info("torrent-downloader healthy (uptime=%.1fs, vpn=bound)", health.uptime_seconds)

    intents = discord.Intents.default()
    bot = commands.Bot(command_prefix="/", intents=intents)

    @bot.event
    async def on_ready() -> None:
        logger.info("Logged in as %s", bot.user)

    try:
        await bot.start(config.discord_token)
    finally:
        await client.close()


def main() -> None:
    config = AppConfig()
    asyncio.run(_run(config))
