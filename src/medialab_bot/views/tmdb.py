import discord
from medialab_contracts import MediaType

from medialab_bot.client import OrchestratorClient
from medialab_bot.constants import DISCORD_SELECT_OPTION_MAX_LABEL_LENGTH
from medialab_bot.media import from_tmdb_media_type
from medialab_bot.schemas.tmdb import TmdbSearchResult
from medialab_bot.views.scope import SeasonScopeSelectMenu
from medialab_bot.views.torrent import run_torrent_search

_SEASONS_KEY = "seasons"


class TmdbSelectMenu(discord.ui.View):
    def __init__(
        self,
        results: list[TmdbSearchResult],
        client: OrchestratorClient,
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

        media_type = from_tmdb_media_type(result.media_type)
        if media_type is None:
            await interaction.response.send_message(
                f"Cannot download a '{result.media_type}' result. Pick a movie or show.",
                ephemeral=True,
            )
            return

        await interaction.response.defer(ephemeral=True)

        if media_type is MediaType.SHOW:
            await self._prompt_show_scope(interaction, result)
            return

        await run_torrent_search(
            interaction,
            self._client,
            title=result.title,
            year=result.year,
            media_type=media_type,
            tmdb_id=result.tmdb_id,
            results_per_resolution=self._results_per_resolution,
        )

    async def _prompt_show_scope(
        self, interaction: discord.Interaction, result: TmdbSearchResult
    ) -> None:
        detail = await self._client.search_tmdb_show(result.tmdb_id)
        seasons = (detail.data or {}).get(_SEASONS_KEY, []) if detail is not None else []

        if not seasons:
            # No season list - fall back to a whole-series search rather than dead-ending.
            await run_torrent_search(
                interaction,
                self._client,
                title=result.title,
                year=result.year,
                media_type=MediaType.SHOW,
                tmdb_id=result.tmdb_id,
                results_per_resolution=self._results_per_resolution,
            )
            return

        view = SeasonScopeSelectMenu(
            client=self._client,
            seasons=seasons,
            title=result.title,
            year=result.year,
            tmdb_id=result.tmdb_id,
            results_per_resolution=self._results_per_resolution,
        )
        await interaction.edit_original_response(
            content=f"Choose a download scope for **{result.title} ({result.year})**:",
            view=view,
        )
