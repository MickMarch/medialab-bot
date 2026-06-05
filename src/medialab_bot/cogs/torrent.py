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
        await interaction.response.defer(ephemeral=True)
        message = await interaction.followup.send(f"Searching for torrents matching **{query}**...", ephemeral=True)
        response = await self._client.search_torrents(query)

        if response is None or not response.data:
            await message.edit(content="No torrents found. Try a different query.")
            return

        try:
            view = TorrentSelectMenu(
                response.data,
                self._client,
                results_per_resolution=self._config.torrent_results_per_resolution,
            )
        except ValueError:
            await message.edit(content="No valid torrents found. Try a different query.")
            return

        await message.edit(content=f"Torrents for **{query}**:", view=view)
