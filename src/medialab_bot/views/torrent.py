import discord
from medialab_contracts import MediaType

from medialab_bot.client import OrchestratorClient
from medialab_bot.constants import DISCORD_SELECT_OPTION_MAX_LABEL_LENGTH
from medialab_bot.schemas.torrents import TorrentResult


async def run_torrent_search(
    interaction: discord.Interaction,
    client: OrchestratorClient,
    *,
    title: str,
    year: str,
    media_type: MediaType,
    tmdb_id: int,
    results_per_resolution: int,
    season: int | None = None,
    episode: int | None = None,
) -> None:
    """Runs a scoped torrent search and edits the response with the torrent picker.

    Shared by the movie path (no season/episode) and the TV scope pickers. The
    interaction must already be deferred by the caller.
    """
    await interaction.edit_original_response(
        content=f"Searching for torrents matching **{title} ({year})**...",
        view=None,
    )
    # Movie release names carry the year; show release names do not, so a show
    # query is the bare title (the season/episode scope refines it downstream).
    query = title if media_type is MediaType.SHOW else f"{title} {year}"
    response = await client.search_torrents(query, media_type, season=season, episode=episode)

    if response is None or not response.data:
        await interaction.edit_original_response(
            content="No torrents found for that scope. Try a different search.",
        )
        return

    try:
        view = TorrentSelectMenu(
            response.data,
            client,
            results_per_resolution,
            media_type=media_type,
            tmdb_id=tmdb_id,
        )
    except ValueError:
        await interaction.edit_original_response(
            content="No valid torrents found for that scope. Try a different search.",
        )
        return

    await interaction.edit_original_response(
        content=f"Torrents for **{title} ({year})**:",
        view=view,
    )


class TorrentSelectMenu(discord.ui.View):
    def __init__(
        self,
        groups: dict[str, list[TorrentResult]],
        client: OrchestratorClient,
        results_per_resolution: int,
        media_type: MediaType,
        tmdb_id: int,
    ) -> None:
        super().__init__()
        self._client = client
        # Threaded from the TMDB pick: the gateway requires both at download.
        self._media_type = media_type
        self._tmdb_id = tmdb_id
        self._indexed: dict[str, TorrentResult] = {}

        options: list[discord.SelectOption] = []
        for resolution, results in groups.items():
            top = sorted(results, key=lambda r: r.seeders, reverse=True)[:results_per_resolution]
            for i, result in enumerate(top):
                key = f"{resolution}:{i}"
                self._indexed[key] = result
                label = f"{resolution} - {result.file_name}"[
                    :DISCORD_SELECT_OPTION_MAX_LABEL_LENGTH
                ]
                description = f"{result.seeders} seeders"[:DISCORD_SELECT_OPTION_MAX_LABEL_LENGTH]
                options.append(
                    discord.SelectOption(label=label, value=key, description=description)
                )

        if not options:
            raise ValueError("TorrentSelectMenu requires at least one result")

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

        if not result.file_url.startswith("magnet:"):
            await interaction.response.send_message(
                "Invalid torrent link. Please try a different result.",
                ephemeral=True,
            )
            return

        await interaction.response.defer(ephemeral=True)
        response = await self._client.download(result.file_url, self._media_type, self._tmdb_id)
        if response is None:
            await interaction.followup.send(
                "Download request failed. Please try again.",
                ephemeral=True,
            )
            return

        await interaction.followup.send(
            f"Download started: **{result.file_name}**\n"
            f"Track it with `/jobs` (hash `{response.job.torrent_hash}`).",
            ephemeral=True,
        )
