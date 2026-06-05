import discord
from discord import app_commands
from discord.ext import commands

from medialab_bot.client import TorrentDownloaderClient
from medialab_bot.config import AppConfig
from medialab_bot.views.torrent import TorrentSelectMenu


class TorrentCog(commands.Cog):
    def __init__(self, client: TorrentDownloaderClient, config: AppConfig) -> None:
        self._client = client
        self._config = config

    @app_commands.command(name="torrent", description="Search for torrents directly by title")
    async def torrent(self, interaction: discord.Interaction, query: str) -> None:
        await interaction.response.defer()
        response = await self._client.search_torrents(query)

        if response is None or not response.data:
            await interaction.followup.send(
                "No torrents found. Try a different query.",
                ephemeral=True,
            )
            return

        try:
            view = TorrentSelectMenu(
                response.data,
                self._client,
                results_per_resolution=self._config.torrent_results_per_resolution,
            )
        except ValueError:
            await interaction.followup.send(
                "No valid torrents found. Try a different query.",
                ephemeral=True,
            )
            return

        await interaction.followup.send(f"Torrents for **{query}**:", view=view)
