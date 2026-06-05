import asyncio
import logging

import discord
from discord.ext import commands

from medialab_bot.client import TorrentDownloaderClient
from medialab_bot.config import AppConfig
from medialab_bot.cogs.search import SearchCog
from medialab_bot.cogs.status import StatusCog
from medialab_bot.cogs.torrent import TorrentCog


async def _run(config: AppConfig) -> None:
    logger = logging.getLogger(__name__)

    async with TorrentDownloaderClient(
        base_url=config.torrent_downloader_url,
        api_key=config.torrent_downloader_api_key,
        save_path=config.torrent_save_path,
    ) as client:
        health = await client.health()
        if health is None:
            logger.warning("torrent-downloader unreachable at startup")
        elif not health.vpn_interface_bound:
            logger.warning("torrent-downloader reachable but VPN interface not bound")
        else:
            logger.info("torrent-downloader healthy (uptime=%.1fs, vpn=bound)", health.uptime_seconds)

        guild = discord.Object(id=config.discord_guild_id)
        intents = discord.Intents.default()

        class Bot(commands.Bot):
            async def setup_hook(self) -> None:
                await self.add_cog(SearchCog(client, config))
                await self.add_cog(StatusCog(client))
                await self.add_cog(TorrentCog(client, config))
                self.tree.copy_global_to(guild=guild)
                synced = await self.tree.sync(guild=guild)
                logger.info("Synced %d commands to guild %d", len(synced), config.discord_guild_id)

        bot = Bot(command_prefix="/", intents=intents)

        @bot.event
        async def on_ready() -> None:
            logger.info("Logged in as %s", bot.user)

        await bot.start(config.discord_token)


def main() -> None:
    config = AppConfig()
    logging.basicConfig(level=config.log_level.upper())
    asyncio.run(_run(config))
