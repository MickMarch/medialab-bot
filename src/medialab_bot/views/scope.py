"""TV season/episode scope pickers.

After a show is picked the user chooses a download scope - the whole series, a
season, or a single episode - before the torrent search runs. This targets the
search so older seasons are not buried by the latest season's higher-seeded
packs. Movies skip this flow entirely.
"""

from typing import Any

import discord
from medialab_contracts import MediaType

from medialab_bot.client import OrchestratorClient
from medialab_bot.constants import (
    DISCORD_SELECT_MAX_OPTIONS,
    DISCORD_SELECT_OPTION_MAX_LABEL_LENGTH,
)
from medialab_bot.views.torrent import run_torrent_search

WHOLE_SERIES_VALUE = "all"
WHOLE_SEASON_VALUE = "season"
SEASON_VALUE_PREFIX = "s:"
EPISODE_VALUE_PREFIX = "e:"
MIN_TARGETABLE_SEASON = 1
_SELECTION_ERROR = "Something went wrong with your selection. Please try again."


class SeasonScopeSelectMenu(discord.ui.View):
    """Picks the whole series or a specific season for a show download."""

    def __init__(
        self,
        *,
        client: OrchestratorClient,
        seasons: list[dict[str, Any]],
        title: str,
        year: str,
        tmdb_id: int,
        results_per_resolution: int,
    ) -> None:
        super().__init__()
        self._client = client
        self._title = title
        self._year = year
        self._tmdb_id = tmdb_id
        self._results_per_resolution = results_per_resolution
        # Season 0 is Specials - not targetable via an S0N tag, so it is dropped.
        self._seasons = {
            int(s["season_number"]): s
            for s in seasons
            if int(s.get("season_number", 0)) >= MIN_TARGETABLE_SEASON
        }

        options = [
            discord.SelectOption(label="Whole series", value=WHOLE_SERIES_VALUE),
        ]
        for number in sorted(self._seasons):
            season = self._seasons[number]
            episode_count = season.get("episode_count", 0)
            label = f"Season {number}"[:DISCORD_SELECT_OPTION_MAX_LABEL_LENGTH]
            description = f"{episode_count} episodes"[:DISCORD_SELECT_OPTION_MAX_LABEL_LENGTH]
            options.append(
                discord.SelectOption(
                    label=label, value=f"{SEASON_VALUE_PREFIX}{number}", description=description
                )
            )

        self.select = discord.ui.Select(
            placeholder="Choose a season...", options=options[:DISCORD_SELECT_MAX_OPTIONS]
        )
        self.select.callback = self._on_select
        self.add_item(self.select)

    async def _on_select(self, interaction: discord.Interaction) -> None:
        try:
            value = interaction.data["values"][0]
        except (KeyError, IndexError):
            await interaction.response.send_message(_SELECTION_ERROR, ephemeral=True)
            return

        if value == WHOLE_SERIES_VALUE:
            await interaction.response.defer(ephemeral=True)
            await run_torrent_search(
                interaction,
                self._client,
                title=self._title,
                year=self._year,
                media_type=MediaType.SHOW,
                tmdb_id=self._tmdb_id,
                results_per_resolution=self._results_per_resolution,
            )
            return

        try:
            season_number = int(value.removeprefix(SEASON_VALUE_PREFIX))
            episode_count = int(self._seasons[season_number].get("episode_count", 0))
        except (KeyError, ValueError):
            await interaction.response.send_message(_SELECTION_ERROR, ephemeral=True)
            return

        await interaction.response.defer(ephemeral=True)
        view = EpisodeScopeSelectMenu(
            client=self._client,
            episode_count=episode_count,
            season=season_number,
            title=self._title,
            year=self._year,
            tmdb_id=self._tmdb_id,
            results_per_resolution=self._results_per_resolution,
        )
        await interaction.edit_original_response(
            content=f"Choose an episode scope for **{self._title}** Season {season_number}:",
            view=view,
        )


class EpisodeScopeSelectMenu(discord.ui.View):
    """Picks the whole season or a single episode within a chosen season."""

    def __init__(
        self,
        *,
        client: OrchestratorClient,
        episode_count: int,
        season: int,
        title: str,
        year: str,
        tmdb_id: int,
        results_per_resolution: int,
    ) -> None:
        super().__init__()
        self._client = client
        self._season = season
        self._title = title
        self._year = year
        self._tmdb_id = tmdb_id
        self._results_per_resolution = results_per_resolution

        options = [discord.SelectOption(label="Whole season", value=WHOLE_SEASON_VALUE)]
        # Reserve one slot for the whole-season option when capping.
        max_episodes = DISCORD_SELECT_MAX_OPTIONS - len(options)
        for number in range(1, min(episode_count, max_episodes) + 1):
            options.append(
                discord.SelectOption(
                    label=f"Episode {number}"[:DISCORD_SELECT_OPTION_MAX_LABEL_LENGTH],
                    value=f"{EPISODE_VALUE_PREFIX}{number}",
                )
            )

        self.select = discord.ui.Select(placeholder="Choose an episode...", options=options)
        self.select.callback = self._on_select
        self.add_item(self.select)

    async def _on_select(self, interaction: discord.Interaction) -> None:
        try:
            value = interaction.data["values"][0]
        except (KeyError, IndexError):
            await interaction.response.send_message(_SELECTION_ERROR, ephemeral=True)
            return

        episode: int | None = None
        if value != WHOLE_SEASON_VALUE:
            try:
                episode = int(value.removeprefix(EPISODE_VALUE_PREFIX))
            except ValueError:
                await interaction.response.send_message(_SELECTION_ERROR, ephemeral=True)
                return

        await interaction.response.defer(ephemeral=True)
        await run_torrent_search(
            interaction,
            self._client,
            title=self._title,
            year=self._year,
            media_type=MediaType.SHOW,
            tmdb_id=self._tmdb_id,
            results_per_resolution=self._results_per_resolution,
            season=self._season,
            episode=episode,
        )
