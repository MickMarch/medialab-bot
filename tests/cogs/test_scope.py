"""Tests for the TV season/episode scope pickers."""

from unittest.mock import AsyncMock

import pytest
from medialab_contracts import MediaType

from medialab_bot.schemas.torrents import TorrentResult, TorrentSearchResponse
from medialab_bot.views.scope import EpisodeScopeSelectMenu, SeasonScopeSelectMenu
from medialab_bot.views.torrent import TorrentSelectMenu
from tests.helpers import make_interaction

SHOW_SEASONS = [
    {"season_number": 0, "name": "Specials", "episode_count": 3},
    {"season_number": 1, "name": "Season 1", "episode_count": 13},
    {"season_number": 2, "name": "Season 2", "episode_count": 12},
]


def _torrent_response() -> TorrentSearchResponse:
    result = TorrentResult(
        file_name="The.Wire.S02.1080p.mkv",
        file_url="magnet:?xt=urn:btih:abc",
        seeders=100,
        leechers=5,
        file_size=8_000_000_000,
    )
    return TorrentSearchResponse(status="success", message="", data={"1080p": [result]})


def _season_view(client, seasons=SHOW_SEASONS) -> SeasonScopeSelectMenu:
    return SeasonScopeSelectMenu(
        client=client,
        seasons=seasons,
        title="The Wire",
        year="2002",
        tmdb_id=1438,
        results_per_resolution=5,
    )


def _episode_view(client, episode_count=12) -> EpisodeScopeSelectMenu:
    return EpisodeScopeSelectMenu(
        client=client,
        episode_count=episode_count,
        season=2,
        title="The Wire",
        year="2002",
        tmdb_id=1438,
        results_per_resolution=5,
    )


class TestSeasonScopeOptions:
    def test_lists_whole_series_plus_real_seasons_only(self, mock_client):
        view = _season_view(mock_client)
        values = [o.value for o in view.select.options]
        assert "all" in values
        assert "s:1" in values
        assert "s:2" in values
        # Season 0 (Specials) is not season-targetable via S00.
        assert "s:0" not in values

    def test_caps_options_at_discord_limit(self, mock_client):
        many = [{"season_number": n, "name": f"S{n}", "episode_count": 10} for n in range(1, 40)]
        view = _season_view(mock_client, seasons=many)
        assert len(view.select.options) <= 25


class TestSeasonScopeSelection:
    @pytest.mark.asyncio
    async def test_whole_series_searches_without_season(self, mock_client):
        mock_client.search_torrents = AsyncMock(return_value=_torrent_response())
        view = _season_view(mock_client)
        interaction = make_interaction()
        interaction.configure_mock(data={"values": ["all"]})

        await view.select.callback(interaction)

        mock_client.search_torrents.assert_awaited_once()
        kwargs = mock_client.search_torrents.await_args.kwargs
        args = mock_client.search_torrents.await_args.args
        assert MediaType.SHOW in args or kwargs.get("media_type") is MediaType.SHOW
        assert kwargs.get("season") is None
        assert kwargs.get("episode") is None

    @pytest.mark.asyncio
    async def test_show_search_query_is_bare_title_without_year(self, mock_client):
        # Show torrent queries never carry the year - release names do not
        # include the series' premiere year, so "The Wire 2002" finds nothing.
        mock_client.search_torrents = AsyncMock(return_value=_torrent_response())
        view = _season_view(mock_client)
        interaction = make_interaction()
        interaction.configure_mock(data={"values": ["all"]})

        await view.select.callback(interaction)

        args = mock_client.search_torrents.await_args.args
        assert args[0] == "The Wire"

    @pytest.mark.asyncio
    async def test_whole_series_forwards_torrent_picker(self, mock_client):
        mock_client.search_torrents = AsyncMock(return_value=_torrent_response())
        view = _season_view(mock_client)
        interaction = make_interaction()
        interaction.configure_mock(data={"values": ["all"]})

        await view.select.callback(interaction)

        forwarded = interaction.edit_original_response.call_args_list[-1].kwargs["view"]
        assert isinstance(forwarded, TorrentSelectMenu)

    @pytest.mark.asyncio
    async def test_season_pick_opens_episode_menu(self, mock_client):
        view = _season_view(mock_client)
        interaction = make_interaction()
        interaction.configure_mock(data={"values": ["s:2"]})

        await view.select.callback(interaction)

        forwarded = interaction.edit_original_response.call_args_list[-1].kwargs["view"]
        assert isinstance(forwarded, EpisodeScopeSelectMenu)
        # No search happens yet - the user still has to pick episode-vs-whole-season.
        mock_client.search_torrents.assert_not_called()

    @pytest.mark.asyncio
    async def test_handles_malformed_value(self, mock_client):
        view = _season_view(mock_client)
        interaction = make_interaction()
        interaction.data = {}

        await view.select.callback(interaction)

        interaction.response.send_message.assert_awaited_once()


class TestEpisodeScopeOptions:
    def test_lists_whole_season_plus_episodes(self, mock_client):
        view = _episode_view(mock_client, episode_count=3)
        values = [o.value for o in view.select.options]
        assert "season" in values
        assert "e:1" in values
        assert "e:3" in values

    def test_caps_options_at_discord_limit(self, mock_client):
        view = _episode_view(mock_client, episode_count=100)
        assert len(view.select.options) <= 25


class TestEpisodeScopeSelection:
    @pytest.mark.asyncio
    async def test_whole_season_searches_with_season_only(self, mock_client):
        mock_client.search_torrents = AsyncMock(return_value=_torrent_response())
        view = _episode_view(mock_client)
        interaction = make_interaction()
        interaction.configure_mock(data={"values": ["season"]})

        await view.select.callback(interaction)

        kwargs = mock_client.search_torrents.await_args.kwargs
        assert kwargs.get("season") == 2
        assert kwargs.get("episode") is None

    @pytest.mark.asyncio
    async def test_episode_pick_searches_with_season_and_episode(self, mock_client):
        mock_client.search_torrents = AsyncMock(return_value=_torrent_response())
        view = _episode_view(mock_client)
        interaction = make_interaction()
        interaction.configure_mock(data={"values": ["e:5"]})

        await view.select.callback(interaction)

        kwargs = mock_client.search_torrents.await_args.kwargs
        assert kwargs.get("season") == 2
        assert kwargs.get("episode") == 5

    @pytest.mark.asyncio
    async def test_episode_pick_forwards_torrent_picker(self, mock_client):
        mock_client.search_torrents = AsyncMock(return_value=_torrent_response())
        view = _episode_view(mock_client)
        interaction = make_interaction()
        interaction.configure_mock(data={"values": ["e:5"]})

        await view.select.callback(interaction)

        forwarded = interaction.edit_original_response.call_args_list[-1].kwargs["view"]
        assert isinstance(forwarded, TorrentSelectMenu)
