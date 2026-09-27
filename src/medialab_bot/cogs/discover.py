from collections.abc import Sequence

import discord
from discord import app_commands
from discord.ext import commands
from medialab_contracts import MediaType

from medialab_bot.client import OrchestratorClient
from medialab_bot.config import AppConfig
from medialab_bot.constants import DISCORD_AUTOCOMPLETE_MAX_CHOICES
from medialab_bot.embeds import title_list_embed
from medialab_bot.views.discover import ListedTitle, TitlePickView, list_line

# Discord option name of /popular's media type; autocomplete reads it from the namespace.
TYPE_OPTION = "type"
DEFAULT_AUTOCOMPLETE_TYPE = MediaType.MOVIE
_TYPE_LABELS = {MediaType.MOVIE: "Movies", MediaType.SHOW: "Shows"}
_TYPE_CHOICES = [
    app_commands.Choice(name=label, value=media_type.value)
    for media_type, label in _TYPE_LABELS.items()
]
_UNAVAILABLE = "Could not reach the title catalogue right now. Please try again in a moment."
_WISHLIST_UNAVAILABLE = "Could not load the wishlist right now. Please try again in a moment."
_NO_TITLES = "No titles found for that choice."
_EMPTY_WISHLIST = "The wishlist is empty. Add titles from `/popular`."
_WISHLIST_HEADING = "Wishlist"


class DiscoverCog(commands.Cog):
    def __init__(self, client: OrchestratorClient, config: AppConfig) -> None:
        self._client = client
        self._config = config

    def _pick_view(self, items: Sequence[ListedTitle]) -> TitlePickView:
        return TitlePickView(
            items,
            self._client,
            max_results=self._config.select_max_results,
            results_per_resolution=self._config.torrent_results_per_resolution,
        )

    async def _send_list(
        self, interaction: discord.Interaction, heading: str, items: Sequence[ListedTitle]
    ) -> None:
        view = self._pick_view(items)
        embed = title_list_embed(heading, [list_line(item) for item in view.titles])
        await interaction.followup.send(embed=embed, view=view, ephemeral=True)

    @app_commands.command(name="popular", description="Browse trending movies or shows")
    @app_commands.rename(media_type=TYPE_OPTION)
    @app_commands.describe(media_type="Movies or shows", genre="Narrow to one genre")
    @app_commands.choices(media_type=_TYPE_CHOICES)
    async def popular(
        self,
        interaction: discord.Interaction,
        media_type: app_commands.Choice[str],
        genre: int | None = None,
    ) -> None:
        await interaction.response.defer(ephemeral=True)
        chosen = MediaType(media_type.value)
        response = await self._client.discover(chosen, genre=genre)
        if response is None:
            await interaction.followup.send(_UNAVAILABLE, ephemeral=True)
            return
        if not response.items:
            await interaction.followup.send(_NO_TITLES, ephemeral=True)
            return
        await self._send_list(
            interaction, f"Popular {_TYPE_LABELS[chosen].lower()}", response.items
        )

    @popular.autocomplete("genre")
    async def genre_autocomplete(
        self, interaction: discord.Interaction, current: str
    ) -> list[app_commands.Choice[int]]:
        typed_type = getattr(interaction.namespace, TYPE_OPTION, None)
        try:
            media_type = MediaType(typed_type) if typed_type else DEFAULT_AUTOCOMPLETE_TYPE
        except ValueError:
            media_type = DEFAULT_AUTOCOMPLETE_TYPE
        response = await self._client.discover_genres(media_type)
        if response is None:
            return []
        needle = current.casefold()
        return [
            app_commands.Choice(name=genre.name, value=genre.id)
            for genre in response.genres
            if needle in genre.name.casefold()
        ][:DISCORD_AUTOCOMPLETE_MAX_CHOICES]

    @app_commands.command(name="wishlist", description="Titles saved for later")
    async def wishlist(self, interaction: discord.Interaction) -> None:
        await interaction.response.defer(ephemeral=True)
        response = await self._client.list_wishlist()
        if response is None:
            await interaction.followup.send(_WISHLIST_UNAVAILABLE, ephemeral=True)
            return
        if not response.items:
            await interaction.followup.send(_EMPTY_WISHLIST, ephemeral=True)
            return
        await self._send_list(interaction, _WISHLIST_HEADING, response.items)
