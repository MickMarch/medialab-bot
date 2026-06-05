import discord
from discord import app_commands
from discord.ext import commands

from medialab_bot.client import TorrentDownloaderClient
from medialab_bot.embeds import search_results_embed
from medialab_bot.schemas.tmdb import TmdbSearchResult
from medialab_bot.schemas.torrents import TorrentResult


class TorrentSelectMenu(discord.ui.View):
    def __init__(self, groups: dict[str, list[TorrentResult]], client: TorrentDownloaderClient) -> None:
        super().__init__()
        self._client = client
        self._indexed: dict[str, TorrentResult] = {}

        options: list[discord.SelectOption] = []
        for resolution, results in groups.items():
            top = sorted(results, key=lambda r: r.nbSeeders, reverse=True)[:5]
            for i, result in enumerate(top):
                key = f"{resolution}:{i}"
                self._indexed[key] = result
                label = f"{resolution} - {result.fileName}"[:100]
                description = f"{result.nbSeeders} seeders"[:100]
                options.append(discord.SelectOption(label=label, value=key, description=description))

        self.select = discord.ui.Select(placeholder="Choose a torrent...", options=options)
        self.select.callback = self._on_select
        self.add_item(self.select)

    async def _on_select(self, interaction: discord.Interaction) -> None:
        try:
            key = interaction.data["values"][0]
            result = self._indexed[key]
        except (KeyError, IndexError, ValueError):
            await interaction.response.send_message(
                "Something went wrong with your selection. Please try again.",
                ephemeral=True,
            )
            return

        response = await self._client.download(result.fileUrl)
        if response is None:
            await interaction.response.send_message(
                "Download request failed. Please try again.",
                ephemeral=True,
            )
            return

        await interaction.response.send_message(
            f"Download started: **{result.fileName}**",
            ephemeral=True,
        )


class TmdbSelectMenu(discord.ui.View):
    def __init__(self, results: list[TmdbSearchResult], client: TorrentDownloaderClient) -> None:
        super().__init__()
        self._client = client
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
        try:
            value = interaction.data["values"][0]
            tmdb_id, _ = value.split(":", 1)
            result = self._results[tmdb_id]
        except (KeyError, IndexError, ValueError):
            await interaction.response.send_message(
                "Something went wrong with your selection. Please try again.",
                ephemeral=True,
            )
            return

        await interaction.response.defer()
        torrent_response = await self._client.search_torrents(f"{result.title} {result.year}")

        if torrent_response is None or not torrent_response.data:
            await interaction.followup.send(
                "No torrents found for that title. Try a different search.",
                ephemeral=True,
            )
            return

        view = TorrentSelectMenu(torrent_response.data, self._client)
        await interaction.followup.send(
            f"Torrents for **{result.title} ({result.year})**:",
            view=view,
        )


class SearchCog(commands.Cog):
    def __init__(self, client: TorrentDownloaderClient) -> None:
        self._client = client

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
        view = TmdbSelectMenu(response.data, self._client)
        await interaction.followup.send(embed=embed, view=view)
