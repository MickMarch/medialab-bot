import discord
from discord import app_commands
from discord.ext import commands

from medialab_bot.client import TorrentDownloaderClient
from medialab_bot.embeds import search_results_embed
from medialab_bot.schemas.tmdb import TmdbSearchResult


class TmdbSelectMenu(discord.ui.View):
    def __init__(self, results: list[TmdbSearchResult]) -> None:
        super().__init__()
        self._results = {str(r.tmdb_id): r for r in results}

        options = [
            discord.SelectOption(
                label=f"{r.title} ({r.year})"[:100],
                value=f"{r.tmdb_id}:{r.media_type}",
                description=f"{r.media_type} - ⭐ {r.vote_average}"[:100],
            )
            for r in results[:25]
        ]
        self.select = discord.ui.Select(placeholder="Choose a title...", options=options)
        self.select.callback = self._on_select
        self.add_item(self.select)

    async def _on_select(self, interaction: discord.Interaction) -> None:
        value = interaction.data["values"][0]
        tmdb_id, _ = value.split(":", 1)
        result = self._results[tmdb_id]
        await interaction.response.send_message(
            f"Selected: **{result.title}** ({result.year})",
            ephemeral=True,
        )


class SearchCog(commands.Cog):
    def __init__(self, client: TorrentDownloaderClient) -> None:
        self._client = client

    @app_commands.command(name="search", description="Search TMDB for movies and TV shows")
    async def search(self, interaction: discord.Interaction, query: str) -> None:
        response = await self._client.search_tmdb(query)

        if response is None or not response.data:
            await interaction.response.send_message(
                "No results found. Try a different query.",
                ephemeral=True,
            )
            return

        embed = search_results_embed(response.data)
        view = TmdbSelectMenu(response.data)
        await interaction.response.send_message(embed=embed, view=view)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(SearchCog(bot.torrent_client))
