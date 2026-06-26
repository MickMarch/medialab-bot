import discord

from medialab_bot.client import TorrentDownloaderClient
from medialab_bot.constants import DISCORD_SELECT_OPTION_MAX_LABEL_LENGTH
from medialab_bot.schemas.tmdb import TmdbSearchResult
from medialab_bot.views.torrent import TorrentSelectMenu


class TmdbSelectMenu(discord.ui.View):
    def __init__(
        self,
        results: list[TmdbSearchResult],
        client: TorrentDownloaderClient,
        max_results: int,
        results_per_resolution: int,
    ) -> None:
        super().__init__()
        self._client = client
        self._results_per_resolution = results_per_resolution

        top_results = results[:max_results]
        self._results = {str(r.tmdb_id): r for r in top_results}

        options = [
            discord.SelectOption(
                label=f"{r.title} ({r.year})"[:DISCORD_SELECT_OPTION_MAX_LABEL_LENGTH],
                value=f"{r.tmdb_id}:{r.media_type}",
                description=f"{r.media_type} - ⭐ {r.vote_average}"[
                    :DISCORD_SELECT_OPTION_MAX_LABEL_LENGTH
                ],
            )
            for r in top_results
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

        await interaction.response.defer(ephemeral=True)
        await interaction.edit_original_response(
            content=f"Searching for torrents matching **{result.title} ({result.year})**...",
            view=None,
        )
        torrent_response = await self._client.search_torrents(f"{result.title} {result.year}")

        if torrent_response is None or not torrent_response.data:
            await interaction.edit_original_response(
                content="No torrents found for that title. Try a different search.",
            )
            return

        try:
            view = TorrentSelectMenu(
                torrent_response.data, self._client, self._results_per_resolution
            )
        except ValueError:
            await interaction.edit_original_response(
                content="No valid torrents found for that title. Try a different search.",
            )
            return

        await interaction.edit_original_response(
            content=f"Torrents for **{result.title} ({result.year})**:",
            view=view,
        )
