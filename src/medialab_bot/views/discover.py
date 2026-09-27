"""/popular and /wishlist: pick a title, then Download or toggle it on the wishlist.

Download hands off to the same scope pickers and torrent search as /search.
"""

from collections.abc import Sequence

import discord
from medialab_contracts import DiscoverItem, MediaType, WishlistAddRequest, WishlistItem

from medialab_bot.client import OrchestratorClient
from medialab_bot.constants import (
    DISCORD_SELECT_MAX_OPTIONS,
    DISCORD_SELECT_OPTION_MAX_LABEL_LENGTH,
    IN_LIBRARY_MARKER,
    WISHLIST_MARKER,
)
from medialab_bot.embeds import display_title, title_embed
from medialab_bot.views.scope import prompt_show_scope
from medialab_bot.views.torrent import run_torrent_search

type ListedTitle = DiscoverItem | WishlistItem

DOWNLOAD_LABEL = "Download"
WISHLIST_ADD_LABEL = "Wishlist"
WISHLIST_REMOVE_LABEL = "Remove"
_SEPARATOR = " - "
_VALUE_SEPARATOR = ":"
_SELECTION_ERROR = "Something went wrong with your selection. Please try again."
_WISHLIST_ERROR = "Could not update the wishlist right now. Please try again."


def _rating(item: ListedTitle) -> str | None:
    return f"{item.vote_average:.1f}" if isinstance(item, DiscoverItem) else None


def _is_on_wishlist(item: ListedTitle) -> bool:
    return isinstance(item, WishlistItem) or item.on_wishlist


def _value(item: ListedTitle) -> str:
    return f"{item.media_type.value}{_VALUE_SEPARATOR}{item.tmdb_id}"


def _annotations(item: ListedTitle) -> list[str]:
    parts = []
    rating = _rating(item)
    if rating is not None:
        parts.append(rating)
    if item.in_library:
        parts.append(IN_LIBRARY_MARKER)
    # Every /wishlist item is on the wishlist; the marker only helps in discover lists.
    if isinstance(item, DiscoverItem) and item.on_wishlist:
        parts.append(WISHLIST_MARKER)
    return parts


def list_line(item: ListedTitle) -> str:
    """``Title (year) - rating``, plus the library and wishlist markers when they apply."""
    return _SEPARATOR.join([display_title(item.title, item.year), *_annotations(item)])


def _details(item: ListedTitle) -> str:
    return _SEPARATOR.join([item.media_type.value, *_annotations(item)])


class TitleActionView(discord.ui.View):
    """Download and Wishlist / Remove for one chosen title."""

    def __init__(
        self,
        client: OrchestratorClient,
        item: ListedTitle,
        results_per_resolution: int,
        on_wishlist: bool,
    ) -> None:
        super().__init__()
        self._client = client
        self._item = item
        self._results_per_resolution = results_per_resolution
        self._on_wishlist = on_wishlist

        self.download_button: discord.ui.Button = discord.ui.Button(
            label=DOWNLOAD_LABEL, style=discord.ButtonStyle.primary
        )
        self.download_button.callback = self._on_download
        self.add_item(self.download_button)

        self.wishlist_button: discord.ui.Button = discord.ui.Button()
        self.wishlist_button.callback = self._on_toggle_wishlist
        self._render_wishlist_button()
        self.add_item(self.wishlist_button)

    def _render_wishlist_button(self) -> None:
        if self._on_wishlist:
            self.wishlist_button.label = WISHLIST_REMOVE_LABEL
            self.wishlist_button.style = discord.ButtonStyle.danger
        else:
            self.wishlist_button.label = WISHLIST_ADD_LABEL
            self.wishlist_button.style = discord.ButtonStyle.secondary

    async def _on_download(self, interaction: discord.Interaction) -> None:
        await interaction.response.defer(ephemeral=True)
        item = self._item
        year = item.year or ""
        if item.media_type is MediaType.SHOW:
            await prompt_show_scope(
                interaction,
                self._client,
                title=item.title,
                year=year,
                tmdb_id=item.tmdb_id,
                results_per_resolution=self._results_per_resolution,
            )
            return
        await run_torrent_search(
            interaction,
            self._client,
            title=item.title,
            year=year,
            media_type=item.media_type,
            tmdb_id=item.tmdb_id,
            results_per_resolution=self._results_per_resolution,
        )

    async def _on_toggle_wishlist(self, interaction: discord.Interaction) -> None:
        await interaction.response.defer(ephemeral=True)
        item = self._item
        if self._on_wishlist:
            ok = await self._client.remove_from_wishlist(item.media_type, item.tmdb_id)
        else:
            request = WishlistAddRequest(
                title=item.title,
                year=item.year,
                poster_path=item.poster_path,
                overview=item.overview,
            )
            ok = (
                await self._client.add_to_wishlist(item.media_type, item.tmdb_id, request)
                is not None
            )

        if not ok:
            await interaction.followup.send(_WISHLIST_ERROR, ephemeral=True)
            return

        self._on_wishlist = not self._on_wishlist
        self._render_wishlist_button()
        await interaction.edit_original_response(view=self)


class TitlePickView(discord.ui.View):
    """Select menu over a discover or wishlist list; the pick opens a TitleActionView."""

    def __init__(
        self,
        items: Sequence[ListedTitle],
        client: OrchestratorClient,
        max_results: int,
        results_per_resolution: int,
    ) -> None:
        super().__init__()
        self._client = client
        self._results_per_resolution = results_per_resolution
        self.titles = list(items)[: min(max_results, DISCORD_SELECT_MAX_OPTIONS)]
        self._by_value = {_value(item): item for item in self.titles}

        options = [
            discord.SelectOption(
                label=display_title(item.title, item.year)[:DISCORD_SELECT_OPTION_MAX_LABEL_LENGTH],
                value=value,
                description=_details(item)[:DISCORD_SELECT_OPTION_MAX_LABEL_LENGTH],
            )
            for value, item in self._by_value.items()
        ]
        self.select = discord.ui.Select(placeholder="Choose a title...", options=options)
        self.select.callback = self._on_select
        self.add_item(self.select)

    async def _on_select(self, interaction: discord.Interaction) -> None:
        try:
            item = self._by_value[interaction.data["values"][0]]
        except (KeyError, IndexError, TypeError):
            await interaction.response.send_message(_SELECTION_ERROR, ephemeral=True)
            return

        await interaction.response.defer(ephemeral=True)
        footer = IN_LIBRARY_MARKER.capitalize() if item.in_library else None
        embed = title_embed(
            item.title,
            item.year,
            overview=item.overview,
            poster_path=item.poster_path,
            footer=footer,
        )
        view = TitleActionView(
            self._client,
            item,
            results_per_resolution=self._results_per_resolution,
            on_wishlist=_is_on_wishlist(item),
        )
        await interaction.followup.send(embed=embed, view=view, ephemeral=True)
