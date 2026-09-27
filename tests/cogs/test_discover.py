from datetime import UTC, datetime
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import pytest
from discord import app_commands
from medialab_contracts import (
    DiscoverItem,
    DiscoverResponse,
    Genre,
    GenresResponse,
    MediaType,
    PosterSize,
    WishlistAddRequest,
    WishlistItem,
    WishlistResponse,
    poster_url,
)

from medialab_bot.cogs.discover import DiscoverCog
from medialab_bot.constants import DISCORD_AUTOCOMPLETE_MAX_CHOICES, WISHLIST_MARKER
from medialab_bot.views.discover import (
    WISHLIST_ADD_LABEL,
    WISHLIST_REMOVE_LABEL,
    TitleActionView,
    TitlePickView,
)
from tests.helpers import make_interaction

_NOW = datetime(2026, 9, 27, tzinfo=UTC)
_POSTER = "/dune.jpg"
_MOVIE = app_commands.Choice(name="Movie", value=MediaType.MOVIE.value)
_SHOW = app_commands.Choice(name="Show", value=MediaType.SHOW.value)


def _item(
    tmdb_id: int = 1,
    title: str = "Dune",
    media_type: MediaType = MediaType.MOVIE,
    poster_path: str | None = _POSTER,
    in_library: bool = False,
    on_wishlist: bool = False,
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
        on_wishlist=on_wishlist,
    )


def _wish(tmdb_id: int = 1, media_type: MediaType = MediaType.MOVIE) -> WishlistItem:
    return WishlistItem(
        tmdb_id=tmdb_id,
        media_type=media_type,
        title="Dune",
        year="2021",
        poster_path=_POSTER,
        overview="Sand.",
        added_at=_NOW,
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
async def test_popular_marks_wishlisted_titles_in_list_and_select(mock_client, mock_config):
    items = [_item(1, "Dune", on_wishlist=True), _item(2, "Arrival")]
    mock_client.discover = AsyncMock(return_value=_discover(items))
    cog = DiscoverCog(mock_client, mock_config)
    interaction = make_interaction()

    await cog.popular.callback(cog, interaction, media_type=_MOVIE, genre=None)

    kwargs = _sent_kwargs(interaction)
    lines = kwargs["embed"].description.splitlines()
    assert WISHLIST_MARKER in lines[0]
    assert WISHLIST_MARKER not in lines[1]
    options = kwargs["view"].select.options
    assert WISHLIST_MARKER in (options[0].description or "")
    assert WISHLIST_MARKER not in (options[1].description or "")


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


@pytest.mark.asyncio
async def test_select_title_shows_both_buttons_and_thumbnail(mock_client):
    view = _pick_view(mock_client, [_item()])
    interaction = make_interaction()
    interaction.data = {"values": [view.select.options[0].value]}

    await view._on_select(interaction)

    kwargs = _sent_kwargs(interaction)
    assert kwargs["ephemeral"] is True
    action = kwargs["view"]
    assert isinstance(action, TitleActionView)
    assert action.download_button in action.children
    assert action.wishlist_button in action.children
    assert action.wishlist_button.label == WISHLIST_ADD_LABEL
    embed = kwargs["embed"]
    assert embed.thumbnail.url == poster_url(_POSTER, PosterSize.THUMBNAIL)
    assert embed.description == "Sand."


@pytest.mark.asyncio
async def test_select_title_without_poster_has_no_thumbnail(mock_client):
    view = _pick_view(mock_client, [_item(poster_path=None)])
    interaction = make_interaction()
    interaction.data = {"values": [view.select.options[0].value]}

    await view._on_select(interaction)

    assert _sent_kwargs(interaction)["embed"].thumbnail.url is None


@pytest.mark.asyncio
async def test_select_title_already_on_wishlist_offers_remove(mock_client):
    view = _pick_view(mock_client, [_item(on_wishlist=True)])
    interaction = make_interaction()
    interaction.data = {"values": [view.select.options[0].value]}

    await view._on_select(interaction)

    assert _sent_kwargs(interaction)["view"].wishlist_button.label == WISHLIST_REMOVE_LABEL


@pytest.mark.asyncio
async def test_select_handles_malformed_data(mock_client):
    view = _pick_view(mock_client, [_item()])
    interaction = make_interaction()
    interaction.data = {}

    await view._on_select(interaction)

    assert interaction.response.send_message.call_args.kwargs.get("ephemeral") is True
    interaction.followup.send.assert_not_awaited()


# --- title actions ---


def _action_view(mock_client, item, on_wishlist: bool = False) -> TitleActionView:
    return TitleActionView(mock_client, item, results_per_resolution=5, on_wishlist=on_wishlist)


@pytest.mark.asyncio
async def test_wishlist_button_puts_then_flips_to_remove(mock_client):
    mock_client.add_to_wishlist = AsyncMock(return_value=_wish())
    view = _action_view(mock_client, _item())
    interaction = make_interaction()

    await view.wishlist_button.callback(interaction)

    mock_client.add_to_wishlist.assert_awaited_once_with(
        MediaType.MOVIE,
        1,
        WishlistAddRequest(title="Dune", year="2021", poster_path=_POSTER, overview="Sand."),
    )
    assert view.wishlist_button.label == WISHLIST_REMOVE_LABEL
    interaction.edit_original_response.assert_awaited_once_with(view=view)


@pytest.mark.asyncio
async def test_remove_button_deletes_then_flips_back(mock_client):
    mock_client.remove_from_wishlist = AsyncMock(return_value=True)
    view = _action_view(mock_client, _item(on_wishlist=True), on_wishlist=True)
    interaction = make_interaction()

    await view.wishlist_button.callback(interaction)

    mock_client.remove_from_wishlist.assert_awaited_once_with(MediaType.MOVIE, 1)
    assert view.wishlist_button.label == WISHLIST_ADD_LABEL


@pytest.mark.asyncio
async def test_wishlist_button_failure_keeps_label_and_reports(mock_client):
    mock_client.add_to_wishlist = AsyncMock(return_value=None)
    view = _action_view(mock_client, _item())
    interaction = make_interaction()

    await view.wishlist_button.callback(interaction)

    assert view.wishlist_button.label == WISHLIST_ADD_LABEL
    assert interaction.followup.send.call_args.kwargs.get("ephemeral") is True


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


# --- /wishlist ---


@pytest.mark.asyncio
async def test_wishlist_lists_items_with_select(mock_client, mock_config):
    mock_client.list_wishlist = AsyncMock(
        return_value=WishlistResponse(items=[_wish(1), _wish(2, MediaType.SHOW)])
    )
    cog = DiscoverCog(mock_client, mock_config)
    interaction = make_interaction()

    await cog.wishlist.callback(cog, interaction)

    kwargs = _sent_kwargs(interaction)
    assert kwargs["ephemeral"] is True
    assert isinstance(kwargs["view"], TitlePickView)
    assert len(kwargs["view"].select.options) == 2
    assert len(kwargs["embed"].description.splitlines()) == 2
    assert all(WISHLIST_MARKER in line for line in kwargs["embed"].description.splitlines())


@pytest.mark.asyncio
async def test_wishlist_empty_says_so(mock_client, mock_config):
    mock_client.list_wishlist = AsyncMock(return_value=WishlistResponse(items=[]))
    cog = DiscoverCog(mock_client, mock_config)
    interaction = make_interaction()

    await cog.wishlist.callback(cog, interaction)

    assert "view" not in _sent_kwargs(interaction)


@pytest.mark.asyncio
async def test_wishlist_client_failure_shows_friendly_message(mock_client, mock_config):
    mock_client.list_wishlist = AsyncMock(return_value=None)
    cog = DiscoverCog(mock_client, mock_config)
    interaction = make_interaction()

    await cog.wishlist.callback(cog, interaction)

    assert "view" not in _sent_kwargs(interaction)
    assert "try again" in interaction.followup.send.call_args.args[0].lower()


@pytest.mark.asyncio
async def test_wishlist_chosen_item_offers_download_and_remove(mock_client):
    view = _pick_view(mock_client, [_wish(5, MediaType.SHOW)])
    interaction = make_interaction()
    interaction.data = {"values": [view.select.options[0].value]}

    await view._on_select(interaction)

    kwargs = _sent_kwargs(interaction)
    action = kwargs["view"]
    assert action.download_button in action.children
    assert action.wishlist_button.label == WISHLIST_REMOVE_LABEL
    assert kwargs["embed"].thumbnail.url == poster_url(_POSTER, PosterSize.THUMBNAIL)


@pytest.mark.asyncio
async def test_wishlist_remove_calls_delete(mock_client):
    mock_client.remove_from_wishlist = AsyncMock(return_value=True)
    pick = _pick_view(mock_client, [_wish(5, MediaType.SHOW)])
    interaction = make_interaction()
    interaction.data = {"values": [pick.select.options[0].value]}
    await pick._on_select(interaction)
    action = _sent_kwargs(interaction)["view"]

    await action.wishlist_button.callback(make_interaction())

    mock_client.remove_from_wishlist.assert_awaited_once_with(MediaType.SHOW, 5)
