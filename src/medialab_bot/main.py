import asyncio
import logging

import discord
from discord.errors import LoginFailure
from discord.ext import commands

from medialab_bot.client import OrchestratorClient
from medialab_bot.cogs.delete import DeleteCog
from medialab_bot.cogs.discover import DiscoverCog
from medialab_bot.cogs.jobs import JobsCog
from medialab_bot.cogs.search import SearchCog
from medialab_bot.cogs.settings import SettingsCog
from medialab_bot.cogs.status import StatusCog
from medialab_bot.config import AppConfig
from medialab_bot.startup import RetryPolicy, report_login, start_with_retry


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
                "torrent-downloader=%s, medialab-jellyfin=%s; vpn=%s",
                health.uptime_seconds,
                "up" if down.torrent_downloader else "down",
                "up" if down.medialab_jellyfin else "down",
                "bound" if health.vpn_interface_bound else "not bound",
            )
            if not health.vpn_interface_bound:
                logger.warning("VPN is not bound; torrent-downloader will refuse downloads")
            if health.needs_attention:
                logger.warning(
                    "%d job(s) need attention; see /jobs NEEDS_ATTENTION", health.needs_attention
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
                await self.add_cog(DeleteCog(client))
                await self.add_cog(DiscoverCog(client, config))
                await self.add_cog(SettingsCog(client))
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
            await report_login(client, ok=True)

        policy = RetryPolicy(
            max_attempts=config.login_max_attempts,
            base_delay_seconds=config.login_backoff_base_seconds,
            max_delay_seconds=config.login_backoff_max_seconds,
        )
        try:
            await start_with_retry(lambda: bot.start(config.discord_token), policy)
        except LoginFailure as exc:
            await report_login(client, ok=False, detail=str(exc))
            raise
        finally:
            logger.info("bot shutting down")


def main() -> None:
    config = AppConfig()
    logging.basicConfig(level=config.log_level.upper())
    asyncio.run(_run(config))
