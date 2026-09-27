"""/popular and /watchlist: pick a title, then Download, Save / Unsave, or Follow / Unfollow.

Download hands off to the same scope pickers and torrent search as /search. Follow is
one tap: new episodes only at the default resolution. Every other follow control lives
in the web UI.
"""

from collections.abc import Sequence

import discord
from medialab_contracts import (
    DEFAULT_FOLLOW_RESOLUTION,
    DiscoverItem,
    FollowRequest,
    FollowStart,
    FollowStartMode,
    MediaType,
    WatchlistAddRequest,
    WatchlistItem,
    WatchlistKind,
)

from medialab_bot.client import OrchestratorClient
from medialab_bot.constants import (
    DISCORD_SELECT_MAX_OPTIONS,
    DISCORD_SELECT_OPTION_MAX_LABEL_LENGTH,
    IN_LIBRARY_MARKER,
)
from medialab_bot.embeds import display_title, title_embed, watchlist_marker
from medialab_bot.views.scope import prompt_show_scope
from medialab_bot.views.torrent import run_torrent_search

type ListedTitle = DiscoverItem | WatchlistItem

DOWNLOAD_LABEL = "Download"
SAVE_LABEL = "Save"
UNSAVE_LABEL = "Unsave"
FOLLOW_LABEL = "Follow"
UNFOLLOW_LABEL = "Unfollow"
_SEPARATOR = " - "
_VALUE_SEPARATOR = ":"
_LAST_SUBMITTED_PREFIX = "last "
_SELECTION_ERROR = "Something went wrong with your selection. Please try again."
_WATCHLIST_ERROR = "Could not update the watchlist right now. Please try again."
_FOLLOW_ERROR = "Could not update the follow right now. Please try again."
_ONE_TAP_FOLLOW = FollowRequest(
    start=FollowStart(mode=FollowStartMode.NEW_ONLY), resolution=DEFAULT_FOLLOW_RESOLUTION
)


def _rating(item: ListedTitle) -> str | None:
    return f"{item.vote_average:.1f}" if isinstance(item, DiscoverItem) else None


def _is_on_watchlist(item: ListedTitle) -> bool:
    return isinstance(item, WatchlistItem) or item.on_watchlist


def _is_following(item: ListedTitle) -> bool:
    kind = item.kind if isinstance(item, WatchlistItem) else item.watchlist_kind
    return kind is WatchlistKind.FOLLOWING


def _value(item: ListedTitle) -> str:
    return f"{item.media_type.value}{_VALUE_SEPARATOR}{item.tmdb_id}"


def _watchlist_annotations(item: ListedTitle) -> list[str]:
    if isinstance(item, DiscoverItem):
        return [watchlist_marker(item.watchlist_kind)] if item.on_watchlist else []
    # Every /watchlist item is saved; only a follow is worth calling out there.
    if not _is_following(item):
        return []
    parts = [watchlist_marker(item.kind)]
    if item.follow is not None and item.follow.last_submitted:
        parts.append(f"{_LAST_SUBMITTED_PREFIX}{item.follow.last_submitted}")
    return parts


def _annotations(item: ListedTitle) -> list[str]:
    parts = []
    rating = _rating(item)
    if rating is not None:
        parts.append(rating)
    if item.in_library:
        parts.append(IN_LIBRARY_MARKER)
    parts.extend(_watchlist_annotations(item))
    return parts


def list_line(item: ListedTitle) -> str:
    """``Title (year) - rating``, plus the library and watchlist markers when they apply."""
    return _SEPARATOR.join([display_title(item.title, item.year), *_annotations(item)])


def _details(item: ListedTitle) -> str:
    return _SEPARATOR.join([item.media_type.value, *_annotations(item)])


class TitleActionView(discord.ui.View):
    """Download, Save / Unsave and, for shows, Follow / Unfollow for one chosen title."""

    def __init__(
        self,
        client: OrchestratorClient,
        item: ListedTitle,
        results_per_resolution: int,
        on_watchlist: bool,
        following: bool = False,
    ) -> None:
        super().__init__()
        self._client = client
        self._item = item
        self._results_per_resolution = results_per_resolution
        self._on_watchlist = on_watchlist
        self._following = following

        self.download_button: discord.ui.Button = discord.ui.Button(
            label=DOWNLOAD_LABEL, style=discord.ButtonStyle.primary
        )
        self.download_button.callback = self._on_download
        self.add_item(self.download_button)

        self.save_button: discord.ui.Button = discord.ui.Button()
        self.save_button.callback = self._on_toggle_save
        self.add_item(self.save_button)

        self.follow_button: discord.ui.Button | None = None
        if item.media_type is MediaType.SHOW:
            self.follow_button = discord.ui.Button()
            self.follow_button.callback = self._on_toggle_follow
            self.add_item(self.follow_button)

        self._render_buttons()

    def _render_buttons(self) -> None:
        if self._on_watchlist:
            self.save_button.label = UNSAVE_LABEL
            self.save_button.style = discord.ButtonStyle.danger
        else:
            self.save_button.label = SAVE_LABEL
            self.save_button.style = discord.ButtonStyle.secondary
        if self.follow_button is None:
            return
        if self._following:
            self.follow_button.label = UNFOLLOW_LABEL
            self.follow_button.style = discord.ButtonStyle.danger
        else:
            self.follow_button.label = FOLLOW_LABEL
            self.follow_button.style = discord.ButtonStyle.success

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

    async def _save(self) -> bool:
        item = self._item
        request = WatchlistAddRequest(
            title=item.title,
            year=item.year,
            poster_path=item.poster_path,
            overview=item.overview,
        )
        saved = await self._client.add_to_watchlist(item.media_type, item.tmdb_id, request)
        self._on_watchlist = saved is not None
        return self._on_watchlist

    async def _show_buttons(self, interaction: discord.Interaction) -> None:
        self._render_buttons()
        await interaction.edit_original_response(view=self)

    async def _on_toggle_save(self, interaction: discord.Interaction) -> None:
        await interaction.response.defer(ephemeral=True)
        item = self._item
        if self._on_watchlist:
            ok = await self._client.remove_from_watchlist(item.media_type, item.tmdb_id)
            if ok:
                # Removing the row drops any follow with it.
                self._on_watchlist = False
                self._following = False
        else:
            ok = await self._save()

        if not ok:
            await interaction.followup.send(_WATCHLIST_ERROR, ephemeral=True)
            return
        await self._show_buttons(interaction)

    async def _on_toggle_follow(self, interaction: discord.Interaction) -> None:
        await interaction.response.defer(ephemeral=True)
        tmdb_id = self._item.tmdb_id
        if self._following:
            if not await self._client.unfollow_show(tmdb_id):
                await interaction.followup.send(_FOLLOW_ERROR, ephemeral=True)
                return
            self._following = False
            await self._show_buttons(interaction)
            return

        # The gateway only follows a saved show, so save first when needed.
        if not self._on_watchlist and not await self._save():
            await interaction.followup.send(_WATCHLIST_ERROR, ephemeral=True)
            return
        followed = await self._client.follow_show(tmdb_id, _ONE_TAP_FOLLOW)
        if followed is None:
            # The save above may have succeeded; show that even though the follow failed.
            self._render_buttons()
            await interaction.edit_original_response(view=self)
            await interaction.followup.send(_FOLLOW_ERROR, ephemeral=True)
            return
        self._following = True
        await self._show_buttons(interaction)


class TitlePickView(discord.ui.View):
    """Select menu over a discover or watchlist list; the pick opens a TitleActionView."""

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
            on_watchlist=_is_on_watchlist(item),
            following=_is_following(item),
        )
        await interaction.followup.send(embed=embed, view=view, ephemeral=True)
