import discord
from discord import app_commands
from discord.ext import commands

from medialab_bot.client import TorrentDownloaderClient
from medialab_bot.config import AppConfig
from medialab_bot.embeds import search_results_embed
from medialab_bot.views.tmdb import TmdbSelectMenu


class SearchCog(commands.Cog):
    def __init__(self, client: TorrentDownloaderClient, config: AppConfig) -> None:
        self._client = client
        self._config = config

    @app_commands.command(name="search", description="Search TMDB for movies and TV shows")
    async def search(self, interaction: discord.Interaction, query: str) -> None:
        await interaction.response.defer()
        response = await self._client.search_tmdb(query)

        if response is None or not response.data:
            await interaction.followup.send(
                "No results found. Try a different query.",
                ephemeral=True,
            )
            return

        embed = search_results_embed(response.data)
        view = TmdbSelectMenu(
            response.data,
            self._client,
            max_results=self._config.select_max_results,
            results_per_resolution=self._config.torrent_results_per_resolution,
        )
        await interaction.followup.send(embed=embed, view=view)
