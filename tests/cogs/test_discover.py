from datetime import UTC, datetime
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import pytest
from discord import app_commands
from medialab_contracts import (
    DEFAULT_FOLLOW_RESOLUTION,
    DiscoverItem,
    DiscoverResponse,
    FollowRequest,
    FollowStart,
    FollowStartMode,
    FollowState,
    Genre,
    GenresResponse,
    MediaType,
    PosterSize,
    WatchlistAddRequest,
    WatchlistItem,
    WatchlistKind,
    WatchlistResponse,
    poster_url,
)

from medialab_bot.cogs.discover import DiscoverCog
from medialab_bot.constants import (
    DISCORD_AUTOCOMPLETE_MAX_CHOICES,
    FOLLOWING_MARKER,
    SAVED_MARKER,
)
from medialab_bot.views.discover import (
    FOLLOW_LABEL,
    SAVE_LABEL,
    UNFOLLOW_LABEL,
    UNSAVE_LABEL,
    TitleActionView,
    TitlePickView,
)
from tests.helpers import make_interaction

_NOW = datetime(2026, 9, 27, tzinfo=UTC)
_POSTER = "/dune.jpg"
_MOVIE = app_commands.Choice(name="Movie", value=MediaType.MOVIE.value)
_SHOW = app_commands.Choice(name="Show", value=MediaType.SHOW.value)
_SAVED = app_commands.Choice(name="Saved", value=WatchlistKind.SAVED.value)
_FOLLOWING = app_commands.Choice(name="Following", value=WatchlistKind.FOLLOWING.value)
_NEW_ONLY_FOLLOW = FollowRequest(
    start=FollowStart(mode=FollowStartMode.NEW_ONLY), resolution=DEFAULT_FOLLOW_RESOLUTION
)


def _item(
    tmdb_id: int = 1,
    title: str = "Dune",
    media_type: MediaType = MediaType.MOVIE,
    poster_path: str | None = _POSTER,
    in_library: bool = False,
    on_watchlist: bool = False,
    watchlist_kind: WatchlistKind | None = None,
) -> DiscoverItem:
    return DiscoverItem(
        tmdb_id=tmdb_id,
        media_type=media_type,
        title=title,
        year="2021",
        overview="Sand.",
        vote_average=7.8,
        poster_path=poster_path,
        in_library=in_library,
        on_watchlist=on_watchlist,
        watchlist_kind=watchlist_kind,
    )


def _saved(tmdb_id: int = 1, media_type: MediaType = MediaType.MOVIE) -> WatchlistItem:
    return WatchlistItem(
        tmdb_id=tmdb_id,
        media_type=media_type,
        title="Dune",
        year="2021",
        poster_path=_POSTER,
        overview="Sand.",
        added_at=_NOW,
    )


def _followed(tmdb_id: int = 1, last_submitted: str | None = None) -> WatchlistItem:
    return WatchlistItem(
        tmdb_id=tmdb_id,
        media_type=MediaType.SHOW,
        kind=WatchlistKind.FOLLOWING,
        title="Dune",
        year="2021",
        poster_path=_POSTER,
        overview="Sand.",
        added_at=_NOW,
        follow=FollowState(
            start=FollowStart(mode=FollowStartMode.NEW_ONLY),
            followed_at=_NOW,
            last_submitted=last_submitted,
        ),
    )


def _discover(items: list[DiscoverItem]) -> DiscoverResponse:
    return DiscoverResponse(items=items, page=1, total_pages=1, cached_at=_NOW)


def _sent_kwargs(interaction) -> dict:
    return interaction.followup.send.call_args.kwargs


# --- /popular ---


@pytest.mark.asyncio
async def test_popular_passes_type_and_genre_to_client(mock_client, mock_config):
    mock_client.discover = AsyncMock(return_value=_discover([_item()]))
    cog = DiscoverCog(mock_client, mock_config)
    interaction = make_interaction()

    await cog.popular.callback(cog, interaction, media_type=_SHOW, genre=18)

    interaction.response.defer.assert_awaited_once()
    assert interaction.response.defer.call_args.kwargs.get("ephemeral") is True
    mock_client.discover.assert_awaited_once_with(MediaType.SHOW, genre=18)


@pytest.mark.asyncio
async def test_popular_without_genre_passes_none(mock_client, mock_config):
    mock_client.discover = AsyncMock(return_value=_discover([_item()]))
    cog = DiscoverCog(mock_client, mock_config)

    await cog.popular.callback(cog, make_interaction(), media_type=_MOVIE, genre=None)

    mock_client.discover.assert_awaited_once_with(MediaType.MOVIE, genre=None)


@pytest.mark.asyncio
async def test_popular_lists_titles_with_rating_and_library_marker(mock_client, mock_config):
    items = [_item(1, "Dune", in_library=True), _item(2, "Arrival")]
    mock_client.discover = AsyncMock(return_value=_discover(items))
    cog = DiscoverCog(mock_client, mock_config)
    interaction = make_interaction()

    await cog.popular.callback(cog, interaction, media_type=_MOVIE, genre=None)

    kwargs = _sent_kwargs(interaction)
    assert kwargs["ephemeral"] is True
    assert isinstance(kwargs["view"], TitlePickView)
    lines = kwargs["embed"].description.splitlines()
    assert lines[0].startswith("Dune (2021) - 7.8")
    assert "in Jellyfin" in lines[0]
    assert "in Jellyfin" not in lines[1]


@pytest.mark.asyncio
async def test_popular_marks_saved_and_following_titles(mock_client, mock_config):
    items = [
        _item(1, "Dune", on_watchlist=True, watchlist_kind=WatchlistKind.SAVED),
        _item(2, "Arrival"),
        _item(
            3,
            "Severance",
            media_type=MediaType.SHOW,
            on_watchlist=True,
            watchlist_kind=WatchlistKind.FOLLOWING,
        ),
    ]
    mock_client.discover = AsyncMock(return_value=_discover(items))
    cog = DiscoverCog(mock_client, mock_config)
    interaction = make_interaction()

    await cog.popular.callback(cog, interaction, media_type=_MOVIE, genre=None)

    kwargs = _sent_kwargs(interaction)
    lines = kwargs["embed"].description.splitlines()
    assert SAVED_MARKER in lines[0]
    assert SAVED_MARKER not in lines[1]
    assert FOLLOWING_MARKER in lines[2]
    assert SAVED_MARKER not in lines[2]
    options = kwargs["view"].select.options
    assert SAVED_MARKER in (options[0].description or "")
    assert SAVED_MARKER not in (options[1].description or "")
    assert FOLLOWING_MARKER in (options[2].description or "")


@pytest.mark.asyncio
async def test_popular_marks_watchlisted_title_without_kind_as_saved(mock_client, mock_config):
    mock_client.discover = AsyncMock(return_value=_discover([_item(1, on_watchlist=True)]))
    cog = DiscoverCog(mock_client, mock_config)
    interaction = make_interaction()

    await cog.popular.callback(cog, interaction, media_type=_MOVIE, genre=None)

    assert SAVED_MARKER in _sent_kwargs(interaction)["embed"].description


@pytest.mark.asyncio
async def test_popular_caps_at_select_max_results(mock_client, mock_config):
    mock_config.select_max_results = 3
    items = [_item(i, f"T{i}") for i in range(10)]
    mock_client.discover = AsyncMock(return_value=_discover(items))
    cog = DiscoverCog(mock_client, mock_config)
    interaction = make_interaction()

    await cog.popular.callback(cog, interaction, media_type=_MOVIE, genre=None)

    kwargs = _sent_kwargs(interaction)
    assert len(kwargs["view"].select.options) == 3
    assert len(kwargs["embed"].description.splitlines()) == 3


@pytest.mark.asyncio
async def test_popular_tmdb_unavailable_shows_friendly_message(mock_client, mock_config):
    mock_client.discover = AsyncMock(return_value=None)
    cog = DiscoverCog(mock_client, mock_config)
    interaction = make_interaction()

    await cog.popular.callback(cog, interaction, media_type=_MOVIE, genre=None)

    kwargs = _sent_kwargs(interaction)
    assert kwargs["ephemeral"] is True
    assert "view" not in kwargs
    assert "try again" in interaction.followup.send.call_args.args[0].lower()


@pytest.mark.asyncio
async def test_popular_empty_list_says_so(mock_client, mock_config):
    mock_client.discover = AsyncMock(return_value=_discover([]))
    cog = DiscoverCog(mock_client, mock_config)
    interaction = make_interaction()

    await cog.popular.callback(cog, interaction, media_type=_MOVIE, genre=None)

    assert "view" not in _sent_kwargs(interaction)


# --- genre autocomplete ---


def _genres(*names: str) -> GenresResponse:
    return GenresResponse(genres=[Genre(id=i, name=n) for i, n in enumerate(names)])


@pytest.mark.asyncio
async def test_genre_autocomplete_filters_by_typed_text(mock_client, mock_config):
    mock_client.discover_genres = AsyncMock(return_value=_genres("Action", "Drama", "Adventure"))
    cog = DiscoverCog(mock_client, mock_config)
    interaction = make_interaction()
    interaction.namespace = SimpleNamespace(type=MediaType.SHOW.value)

    choices = await cog.genre_autocomplete(interaction, "ac")

    mock_client.discover_genres.assert_awaited_once_with(MediaType.SHOW)
    assert [c.name for c in choices] == ["Action"]
    assert choices[0].value == 0


@pytest.mark.asyncio
async def test_genre_autocomplete_is_case_insensitive_substring(mock_client, mock_config):
    mock_client.discover_genres = AsyncMock(return_value=_genres("Action", "Drama", "Adventure"))
    cog = DiscoverCog(mock_client, mock_config)
    interaction = make_interaction()
    interaction.namespace = SimpleNamespace(type=MediaType.MOVIE.value)

    choices = await cog.genre_autocomplete(interaction, "A")

    assert [c.name for c in choices] == ["Action", "Drama", "Adventure"]


@pytest.mark.asyncio
async def test_genre_autocomplete_defaults_to_movie(mock_client, mock_config):
    mock_client.discover_genres = AsyncMock(return_value=_genres("Action"))
    cog = DiscoverCog(mock_client, mock_config)
    interaction = make_interaction()
    interaction.namespace = SimpleNamespace()

    await cog.genre_autocomplete(interaction, "")

    mock_client.discover_genres.assert_awaited_once_with(MediaType.MOVIE)


@pytest.mark.asyncio
async def test_genre_autocomplete_caps_at_discord_limit(mock_client, mock_config):
    names = [f"Genre {i}" for i in range(DISCORD_AUTOCOMPLETE_MAX_CHOICES + 10)]
    mock_client.discover_genres = AsyncMock(return_value=_genres(*names))
    cog = DiscoverCog(mock_client, mock_config)
    interaction = make_interaction()
    interaction.namespace = SimpleNamespace(type=MediaType.MOVIE.value)

    choices = await cog.genre_autocomplete(interaction, "genre")

    assert len(choices) == DISCORD_AUTOCOMPLETE_MAX_CHOICES


@pytest.mark.asyncio
async def test_genre_autocomplete_empty_when_client_fails(mock_client, mock_config):
    mock_client.discover_genres = AsyncMock(return_value=None)
    cog = DiscoverCog(mock_client, mock_config)
    interaction = make_interaction()
    interaction.namespace = SimpleNamespace(type=MediaType.MOVIE.value)

    assert await cog.genre_autocomplete(interaction, "a") == []


# --- picking a title ---


def _pick_view(mock_client, items) -> TitlePickView:
    return TitlePickView(items, mock_client, max_results=25, results_per_resolution=5)


async def _pick_first(mock_client, item) -> TitleActionView:
    view = _pick_view(mock_client, [item])
    interaction = make_interaction()
    interaction.data = {"values": [view.select.options[0].value]}
    await view._on_select(interaction)
    return _sent_kwargs(interaction)["view"]


@pytest.mark.asyncio
async def test_select_movie_shows_download_and_save_with_thumbnail(mock_client):
    view = _pick_view(mock_client, [_item()])
    interaction = make_interaction()
    interaction.data = {"values": [view.select.options[0].value]}

    await view._on_select(interaction)

    kwargs = _sent_kwargs(interaction)
    assert kwargs["ephemeral"] is True
    action = kwargs["view"]
    assert isinstance(action, TitleActionView)
    assert action.download_button in action.children
    assert action.save_button in action.children
    assert action.save_button.label == SAVE_LABEL
    assert action.follow_button is None
    embed = kwargs["embed"]
    assert embed.thumbnail.url == poster_url(_POSTER, PosterSize.THUMBNAIL)
    assert embed.description == "Sand."


@pytest.mark.asyncio
async def test_select_show_adds_follow_button(mock_client):
    action = await _pick_first(mock_client, _item(media_type=MediaType.SHOW))

    assert action.follow_button is not None
    assert action.follow_button in action.children
    assert action.follow_button.label == FOLLOW_LABEL


@pytest.mark.asyncio
async def test_select_followed_show_offers_unfollow_and_unsave(mock_client):
    action = await _pick_first(
        mock_client,
        _item(media_type=MediaType.SHOW, on_watchlist=True, watchlist_kind=WatchlistKind.FOLLOWING),
    )

    assert action.save_button.label == UNSAVE_LABEL
    assert action.follow_button.label == UNFOLLOW_LABEL


@pytest.mark.asyncio
async def test_select_title_without_poster_has_no_thumbnail(mock_client):
    view = _pick_view(mock_client, [_item(poster_path=None)])
    interaction = make_interaction()
    interaction.data = {"values": [view.select.options[0].value]}

    await view._on_select(interaction)

    assert _sent_kwargs(interaction)["embed"].thumbnail.url is None


@pytest.mark.asyncio
async def test_select_title_already_saved_offers_unsave(mock_client):
    action = await _pick_first(mock_client, _item(on_watchlist=True))

    assert action.save_button.label == UNSAVE_LABEL


@pytest.mark.asyncio
async def test_select_handles_malformed_data(mock_client):
    view = _pick_view(mock_client, [_item()])
    interaction = make_interaction()
    interaction.data = {}

    await view._on_select(interaction)

    assert interaction.response.send_message.call_args.kwargs.get("ephemeral") is True
    interaction.followup.send.assert_not_awaited()


# --- title actions: save ---


def _action_view(
    mock_client, item, on_watchlist: bool = False, following: bool = False
) -> TitleActionView:
    return TitleActionView(
        mock_client,
        item,
        results_per_resolution=5,
        on_watchlist=on_watchlist,
        following=following,
    )


@pytest.mark.asyncio
async def test_save_button_puts_then_flips_to_unsave(mock_client):
    mock_client.add_to_watchlist = AsyncMock(return_value=_saved())
    view = _action_view(mock_client, _item())
    interaction = make_interaction()

    await view.save_button.callback(interaction)

    mock_client.add_to_watchlist.assert_awaited_once_with(
        MediaType.MOVIE,
        1,
        WatchlistAddRequest(title="Dune", year="2021", poster_path=_POSTER, overview="Sand."),
    )
    assert view.save_button.label == UNSAVE_LABEL
    interaction.edit_original_response.assert_awaited_once_with(view=view)


@pytest.mark.asyncio
async def test_unsave_button_deletes_then_flips_back(mock_client):
    mock_client.remove_from_watchlist = AsyncMock(return_value=True)
    view = _action_view(mock_client, _item(on_watchlist=True), on_watchlist=True)
    interaction = make_interaction()

    await view.save_button.callback(interaction)

    mock_client.remove_from_watchlist.assert_awaited_once_with(MediaType.MOVIE, 1)
    assert view.save_button.label == SAVE_LABEL


@pytest.mark.asyncio
async def test_unsave_on_followed_show_also_resets_follow_button(mock_client):
    mock_client.remove_from_watchlist = AsyncMock(return_value=True)
    view = _action_view(
        mock_client, _item(media_type=MediaType.SHOW), on_watchlist=True, following=True
    )

    await view.save_button.callback(make_interaction())

    assert view.save_button.label == SAVE_LABEL
    assert view.follow_button.label == FOLLOW_LABEL


@pytest.mark.asyncio
async def test_save_button_failure_keeps_label_and_reports(mock_client):
    mock_client.add_to_watchlist = AsyncMock(return_value=None)
    view = _action_view(mock_client, _item())
    interaction = make_interaction()

    await view.save_button.callback(interaction)

    assert view.save_button.label == SAVE_LABEL
    assert interaction.followup.send.call_args.kwargs.get("ephemeral") is True


# --- title actions: follow ---


@pytest.mark.asyncio
async def test_follow_unsaved_show_saves_then_follows_new_only(mock_client):
    mock_client.add_to_watchlist = AsyncMock(return_value=_saved(1, MediaType.SHOW))
    mock_client.follow_show = AsyncMock(return_value=_followed())
    view = _action_view(mock_client, _item(media_type=MediaType.SHOW))
    interaction = make_interaction()

    await view.follow_button.callback(interaction)

    mock_client.add_to_watchlist.assert_awaited_once_with(
        MediaType.SHOW,
        1,
        WatchlistAddRequest(title="Dune", year="2021", poster_path=_POSTER, overview="Sand."),
    )
    mock_client.follow_show.assert_awaited_once_with(1, _NEW_ONLY_FOLLOW)
    assert view.follow_button.label == UNFOLLOW_LABEL
    assert view.save_button.label == UNSAVE_LABEL
    interaction.edit_original_response.assert_awaited_once_with(view=view)


@pytest.mark.asyncio
async def test_follow_saved_show_follows_only(mock_client):
    mock_client.add_to_watchlist = AsyncMock()
    mock_client.follow_show = AsyncMock(return_value=_followed())
    view = _action_view(
        mock_client, _item(media_type=MediaType.SHOW, on_watchlist=True), on_watchlist=True
    )

    await view.follow_button.callback(make_interaction())

    mock_client.add_to_watchlist.assert_not_awaited()
    mock_client.follow_show.assert_awaited_once_with(1, _NEW_ONLY_FOLLOW)
    assert view.follow_button.label == UNFOLLOW_LABEL


@pytest.mark.asyncio
async def test_follow_stops_when_save_fails(mock_client):
    mock_client.add_to_watchlist = AsyncMock(return_value=None)
    mock_client.follow_show = AsyncMock()
    view = _action_view(mock_client, _item(media_type=MediaType.SHOW))
    interaction = make_interaction()

    await view.follow_button.callback(interaction)

    mock_client.follow_show.assert_not_awaited()
    assert view.follow_button.label == FOLLOW_LABEL
    assert view.save_button.label == SAVE_LABEL
    assert interaction.followup.send.call_args.kwargs.get("ephemeral") is True


@pytest.mark.asyncio
async def test_follow_failure_after_save_keeps_saved_and_reports(mock_client):
    mock_client.add_to_watchlist = AsyncMock(return_value=_saved(1, MediaType.SHOW))
    mock_client.follow_show = AsyncMock(return_value=None)
    view = _action_view(mock_client, _item(media_type=MediaType.SHOW))
    interaction = make_interaction()

    await view.follow_button.callback(interaction)

    assert view.follow_button.label == FOLLOW_LABEL
    assert view.save_button.label == UNSAVE_LABEL
    assert interaction.followup.send.call_args.kwargs.get("ephemeral") is True


@pytest.mark.asyncio
async def test_unfollow_calls_delete_and_stays_saved(mock_client):
    mock_client.unfollow_show = AsyncMock(return_value=True)
    mock_client.remove_from_watchlist = AsyncMock()
    view = _action_view(
        mock_client, _item(media_type=MediaType.SHOW), on_watchlist=True, following=True
    )
    interaction = make_interaction()

    await view.follow_button.callback(interaction)

    mock_client.unfollow_show.assert_awaited_once_with(1)
    mock_client.remove_from_watchlist.assert_not_awaited()
    assert view.follow_button.label == FOLLOW_LABEL
    assert view.save_button.label == UNSAVE_LABEL
    interaction.edit_original_response.assert_awaited_once_with(view=view)


@pytest.mark.asyncio
async def test_unfollow_failure_keeps_label_and_reports(mock_client):
    mock_client.unfollow_show = AsyncMock(return_value=False)
    view = _action_view(
        mock_client, _item(media_type=MediaType.SHOW), on_watchlist=True, following=True
    )
    interaction = make_interaction()

    await view.follow_button.callback(interaction)

    assert view.follow_button.label == UNFOLLOW_LABEL
    assert interaction.followup.send.call_args.kwargs.get("ephemeral") is True


@pytest.mark.asyncio
async def test_movie_card_has_no_follow_button(mock_client):
    view = _action_view(mock_client, _item())

    assert view.follow_button is None
    assert len(view.children) == 2


# --- title actions: download ---


@pytest.mark.asyncio
async def test_download_movie_runs_torrent_search(mock_client):
    view = _action_view(mock_client, _item())
    interaction = make_interaction()

    with patch("medialab_bot.views.discover.run_torrent_search", new=AsyncMock()) as search:
        await view.download_button.callback(interaction)

    interaction.response.defer.assert_awaited_once()
    kwargs = search.call_args.kwargs
    assert kwargs["title"] == "Dune"
    assert kwargs["year"] == "2021"
    assert kwargs["media_type"] is MediaType.MOVIE
    assert kwargs["tmdb_id"] == 1


@pytest.mark.asyncio
async def test_download_show_opens_scope_menus(mock_client):
    view = _action_view(mock_client, _item(media_type=MediaType.SHOW))
    interaction = make_interaction()

    with patch("medialab_bot.views.discover.prompt_show_scope", new=AsyncMock()) as scope:
        await view.download_button.callback(interaction)

    kwargs = scope.call_args.kwargs
    assert kwargs["title"] == "Dune"
    assert kwargs["tmdb_id"] == 1


# --- /watchlist ---


@pytest.mark.asyncio
async def test_watchlist_lists_items_with_select(mock_client, mock_config):
    mock_client.list_watchlist = AsyncMock(
        return_value=WatchlistResponse(items=[_saved(1), _saved(2, MediaType.SHOW)])
    )
    cog = DiscoverCog(mock_client, mock_config)
    interaction = make_interaction()

    await cog.watchlist.callback(cog, interaction, kind=None)

    mock_client.list_watchlist.assert_awaited_once_with(kind=None)
    kwargs = _sent_kwargs(interaction)
    assert kwargs["ephemeral"] is True
    assert isinstance(kwargs["view"], TitlePickView)
    assert len(kwargs["view"].select.options) == 2
    lines = kwargs["embed"].description.splitlines()
    assert len(lines) == 2
    assert all(SAVED_MARKER not in line for line in lines)
    assert all(SAVED_MARKER not in (o.description or "") for o in kwargs["view"].select.options)


@pytest.mark.asyncio
async def test_watchlist_passes_kind_filter(mock_client, mock_config):
    mock_client.list_watchlist = AsyncMock(return_value=WatchlistResponse(items=[_followed()]))
    cog = DiscoverCog(mock_client, mock_config)

    await cog.watchlist.callback(cog, make_interaction(), kind=_FOLLOWING)

    mock_client.list_watchlist.assert_awaited_once_with(kind=WatchlistKind.FOLLOWING)


@pytest.mark.asyncio
async def test_watchlist_saved_filter_passes_saved(mock_client, mock_config):
    mock_client.list_watchlist = AsyncMock(return_value=WatchlistResponse(items=[_saved()]))
    cog = DiscoverCog(mock_client, mock_config)

    await cog.watchlist.callback(cog, make_interaction(), kind=_SAVED)

    mock_client.list_watchlist.assert_awaited_once_with(kind=WatchlistKind.SAVED)


@pytest.mark.asyncio
async def test_watchlist_following_line_shows_marker_and_last_submitted(mock_client, mock_config):
    items = [_followed(1, last_submitted="S02E05"), _followed(2), _saved(3)]
    mock_client.list_watchlist = AsyncMock(return_value=WatchlistResponse(items=items))
    cog = DiscoverCog(mock_client, mock_config)
    interaction = make_interaction()

    await cog.watchlist.callback(cog, interaction, kind=None)

    lines = _sent_kwargs(interaction)["embed"].description.splitlines()
    assert FOLLOWING_MARKER in lines[0]
    assert "S02E05" in lines[0]
    assert FOLLOWING_MARKER in lines[1]
    assert "S0" not in lines[1]
    assert FOLLOWING_MARKER not in lines[2]


@pytest.mark.asyncio
async def test_watchlist_empty_says_so(mock_client, mock_config):
    mock_client.list_watchlist = AsyncMock(return_value=WatchlistResponse(items=[]))
    cog = DiscoverCog(mock_client, mock_config)
    interaction = make_interaction()

    await cog.watchlist.callback(cog, interaction, kind=None)

    assert "view" not in _sent_kwargs(interaction)


@pytest.mark.asyncio
async def test_watchlist_client_failure_shows_friendly_message(mock_client, mock_config):
    mock_client.list_watchlist = AsyncMock(return_value=None)
    cog = DiscoverCog(mock_client, mock_config)
    interaction = make_interaction()

    await cog.watchlist.callback(cog, interaction, kind=None)

    assert "view" not in _sent_kwargs(interaction)
    assert "try again" in interaction.followup.send.call_args.args[0].lower()


@pytest.mark.asyncio
async def test_watchlist_chosen_saved_show_offers_download_unsave_and_follow(mock_client):
    view = _pick_view(mock_client, [_saved(5, MediaType.SHOW)])
    interaction = make_interaction()
    interaction.data = {"values": [view.select.options[0].value]}

    await view._on_select(interaction)

    kwargs = _sent_kwargs(interaction)
    action = kwargs["view"]
    assert action.download_button in action.children
    assert action.save_button.label == UNSAVE_LABEL
    assert action.follow_button.label == FOLLOW_LABEL
    assert kwargs["embed"].thumbnail.url == poster_url(_POSTER, PosterSize.THUMBNAIL)


@pytest.mark.asyncio
async def test_watchlist_chosen_followed_show_offers_unfollow(mock_client):
    action = await _pick_first(mock_client, _followed(5))

    assert action.save_button.label == UNSAVE_LABEL
    assert action.follow_button.label == UNFOLLOW_LABEL


@pytest.mark.asyncio
async def test_watchlist_unsave_calls_delete(mock_client):
    mock_client.remove_from_watchlist = AsyncMock(return_value=True)
    action = await _pick_first(mock_client, _saved(5, MediaType.SHOW))

    await action.save_button.callback(make_interaction())

    mock_client.remove_from_watchlist.assert_awaited_once_with(MediaType.SHOW, 5)
