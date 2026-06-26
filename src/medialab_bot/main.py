import asyncio
import logging

import discord
from discord.ext import commands

from medialab_bot.client import OrchestratorClient
from medialab_bot.cogs.jobs import JobsCog
from medialab_bot.cogs.search import SearchCog
from medialab_bot.cogs.status import StatusCog
from medialab_bot.config import AppConfig


async def _run(config: AppConfig) -> None:
    logger = logging.getLogger(__name__)

    async with OrchestratorClient(
        base_url=config.orchestrator_url,
        api_key=config.orchestrator_api_key,
        torrent_search_timeout=config.torrent_search_timeout_seconds,
    ) as client:
        health = await client.health()
        if health is None:
            logger.warning("medialab-orchestrator unreachable at startup")
        else:
            down = health.downstream
            logger.info(
                "orchestrator healthy (uptime=%.1fs); downstream: "
                "torrent-downloader=%s, medialab-jellyfin=%s",
                health.uptime_seconds,
                "up" if down.torrent_downloader else "down",
                "up" if down.medialab_jellyfin else "down",
            )
            if not (down.torrent_downloader and down.medialab_jellyfin):
                logger.warning("one or more downstream workers are unreachable")

        guild = discord.Object(id=config.discord_guild_id)
        intents = discord.Intents.default()

        class Bot(commands.Bot):
            async def setup_hook(self) -> None:
                await self.add_cog(SearchCog(client, config))
                await self.add_cog(StatusCog(client))
                await self.add_cog(JobsCog(client))
                self.tree.copy_global_to(guild=guild)
                synced = await self.tree.sync(guild=guild)
                logger.info(
                    "Synced %d commands to guild %d",
                    len(synced),
                    config.discord_guild_id,
                )

        bot = Bot(command_prefix="/", intents=intents)

        @bot.event
        async def on_ready() -> None:
            logger.info("Logged in as %s", bot.user)

        await bot.start(config.discord_token)


def main() -> None:
    config = AppConfig()
    logging.basicConfig(level=config.log_level.upper())
    asyncio.run(_run(config))
