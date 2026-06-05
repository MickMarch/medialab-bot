import discord
from discord import app_commands
from discord.ext import commands

from medialab_bot.client import TorrentDownloaderClient
from medialab_bot.config import AppConfig
from medialab_bot.views.tmdb import TmdbSelectMenu


class SearchCog(commands.Cog):
    def __init__(self, client: TorrentDownloaderClient, config: AppConfig) -> None:
        self._client = client
        self._config = config

    @app_commands.command(name="search", description="Search TMDB for movies and TV shows")
    async def search(self, interaction: discord.Interaction, query: str) -> None:
        await interaction.response.defer(ephemeral=True)
        message = await interaction.followup.send(f"Searching TMDB for **{query}**...", ephemeral=True)
        response = await self._client.search_tmdb(query)

        if response is None or not response.data:
            await message.edit(content="No results found. Try a different query.")
            return

        view = TmdbSelectMenu(
            response.data,
            self._client,
            max_results=self._config.select_max_results,
            results_per_resolution=self._config.torrent_results_per_resolution,
        )
        await message.edit(content=f"Results for **{query}**:", view=view)
