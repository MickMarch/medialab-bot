import pytest
from unittest.mock import AsyncMock, MagicMock

from medialab_bot.schemas.tmdb import TmdbSearchResponse, TmdbSearchResult
from medialab_bot.schemas.torrents import TorrentResult, TorrentSearchResponse
from medialab_bot.schemas.downloads import DownloadResponse
from medialab_bot.cogs.search import SearchCog
from medialab_bot.views.tmdb import TmdbSelectMenu
from medialab_bot.views.torrent import TorrentSelectMenu
from tests.helpers import make_interaction


def _make_tmdb_result(tmdb_id: int = 1, title: str = "Test Movie", year: str = "2024") -> TmdbSearchResult:
    return TmdbSearchResult(
        tmdb_id=tmdb_id,
        title=title,
        year=year,
        media_type="movie",
        overview="Overview.",
        vote_average=7.0,
        poster_path=None,
    )


def _make_tmdb_response(results: list[TmdbSearchResult]) -> TmdbSearchResponse:
    return TmdbSearchResponse(status="success", message="", data=results)


def _make_torrent_result(
    filename: str = "Dune.2021.1080p.mkv",
    magnet: str = "magnet:?xt=urn:btih:abc",
    seeders: int = 100,
) -> TorrentResult:
    return TorrentResult(
        file_name=filename,
        file_url=magnet,
        seeders=seeders,
        leechers=5,
        file_size=8_000_000_000,
    )


def _make_torrent_response(groups: dict[str, list[TorrentResult]]) -> TorrentSearchResponse:
    return TorrentSearchResponse(status="success", message="", data=groups)


def _tmdb_view(results, client, mock_config) -> TmdbSelectMenu:
    return TmdbSelectMenu(
        results,
        client,
        max_results=mock_config.select_max_results,
        results_per_resolution=mock_config.torrent_results_per_resolution,
    )


def _torrent_view(groups, client, mock_config) -> TorrentSelectMenu:
    return TorrentSelectMenu(groups, client, results_per_resolution=mock_config.torrent_results_per_resolution)


# --- /search command ---

@pytest.mark.asyncio
async def test_search_defers_before_api_call(mock_client, mock_config):
    mock_client.search_tmdb = AsyncMock(return_value=_make_tmdb_response([_make_tmdb_result()]))
    cog = SearchCog(mock_client, mock_config)
    interaction = make_interaction()

    await cog.search.callback(cog, interaction, query="dune")

    interaction.response.defer.assert_awaited_once()


@pytest.mark.asyncio
async def test_search_sends_searching_message_then_edits_with_view(mock_client, mock_config):
    mock_client.search_tmdb = AsyncMock(return_value=_make_tmdb_response([_make_tmdb_result()]))
    cog = SearchCog(mock_client, mock_config)
    interaction = make_interaction()

    await cog.search.callback(cog, interaction, query="dune")

    mock_client.search_tmdb.assert_awaited_once_with("dune")
    interaction.followup.send.assert_awaited_once()
    message = interaction.followup.send.return_value
    message.edit.assert_awaited_once()
    assert message.edit.call_args.kwargs.get("view") is not None


@pytest.mark.asyncio
async def test_search_edits_message_with_error_on_empty_results(mock_client, mock_config):
    mock_client.search_tmdb = AsyncMock(return_value=_make_tmdb_response([]))
    cog = SearchCog(mock_client, mock_config)
    interaction = make_interaction()

    await cog.search.callback(cog, interaction, query="xyzzy")

    message = interaction.followup.send.return_value
    message.edit.assert_awaited_once()


@pytest.mark.asyncio
async def test_search_edits_message_with_error_on_client_none(mock_client, mock_config):
    mock_client.search_tmdb = AsyncMock(return_value=None)
    cog = SearchCog(mock_client, mock_config)
    interaction = make_interaction()

    await cog.search.callback(cog, interaction, query="dune")

    message = interaction.followup.send.return_value
    message.edit.assert_awaited_once()


# --- TmdbSelectMenu ---

@pytest.mark.asyncio
async def test_tmdb_select_calls_torrent_search_with_title_and_year(mock_client, mock_config):
    result = _make_tmdb_result(tmdb_id=42, title="Dune", year="2021")
    mock_client.search_torrents = AsyncMock(
        return_value=_make_torrent_response({"1080p": [_make_torrent_result()]})
    )
    view = _tmdb_view([result], mock_client, mock_config)
    interaction = make_interaction()
    interaction.configure_mock(data={"values": ["42:movie"]})

    await view.select.callback(interaction)

    mock_client.search_torrents.assert_awaited_once_with("Dune 2021")


@pytest.mark.asyncio
async def test_tmdb_select_defers_before_torrent_search(mock_client, mock_config):
    result = _make_tmdb_result(tmdb_id=42, title="Dune", year="2021")
    mock_client.search_torrents = AsyncMock(
        return_value=_make_torrent_response({"1080p": [_make_torrent_result()]})
    )
    view = _tmdb_view([result], mock_client, mock_config)
    interaction = make_interaction()
    interaction.configure_mock(data={"values": ["42:movie"]})

    await view.select.callback(interaction)

    interaction.response.defer.assert_awaited_once()


@pytest.mark.asyncio
async def test_tmdb_select_sends_torrent_picker_on_results(mock_client, mock_config):
    result = _make_tmdb_result(tmdb_id=42, title="Dune", year="2021")
    mock_client.search_torrents = AsyncMock(
        return_value=_make_torrent_response({"1080p": [_make_torrent_result()]})
    )
    view = _tmdb_view([result], mock_client, mock_config)
    interaction = make_interaction()
    interaction.configure_mock(data={"values": ["42:movie"]})

    await view.select.callback(interaction)

    last_edit = interaction.edit_original_response.call_args_list[-1]
    assert last_edit.kwargs.get("view") is not None


@pytest.mark.asyncio
async def test_tmdb_select_edits_message_with_error_on_no_torrents(mock_client, mock_config):
    result = _make_tmdb_result(tmdb_id=42, title="Dune", year="2021")
    mock_client.search_torrents = AsyncMock(return_value=_make_torrent_response({}))
    view = _tmdb_view([result], mock_client, mock_config)
    interaction = make_interaction()
    interaction.configure_mock(data={"values": ["42:movie"]})

    await view.select.callback(interaction)

    interaction.edit_original_response.assert_awaited()


@pytest.mark.asyncio
async def test_tmdb_select_edits_message_with_error_on_client_none(mock_client, mock_config):
    result = _make_tmdb_result(tmdb_id=42, title="Dune", year="2021")
    mock_client.search_torrents = AsyncMock(return_value=None)
    view = _tmdb_view([result], mock_client, mock_config)
    interaction = make_interaction()
    interaction.configure_mock(data={"values": ["42:movie"]})

    await view.select.callback(interaction)

    interaction.edit_original_response.assert_awaited()


@pytest.mark.asyncio
async def test_tmdb_select_handles_malformed_data(mock_client, mock_config):
    view = _tmdb_view([_make_tmdb_result(tmdb_id=42)], mock_client, mock_config)
    interaction = make_interaction()
    interaction.data = {}

    await view.select.callback(interaction)

    interaction.response.send_message.assert_awaited_once()
    assert interaction.response.send_message.call_args.kwargs.get("ephemeral") is True


# --- TorrentSelectMenu ---

@pytest.mark.asyncio
async def test_torrent_select_calls_download_with_correct_magnet(mock_client, mock_config):
    groups = {
        "1080p": [
            _make_torrent_result(magnet="magnet:?xt=urn:btih:aaa", seeders=200),
            _make_torrent_result(magnet="magnet:?xt=urn:btih:bbb", seeders=100),
        ],
        "720p": [
            _make_torrent_result(magnet="magnet:?xt=urn:btih:ccc", seeders=50),
        ],
    }
    mock_client.download = AsyncMock(return_value=DownloadResponse(status="success", message="Added."))
    view = _torrent_view(groups, mock_client, mock_config)
    interaction = make_interaction()
    interaction.configure_mock(data={"values": ["1080p:1"]})

    await view.select.callback(interaction)

    mock_client.download.assert_awaited_once_with("magnet:?xt=urn:btih:bbb")


@pytest.mark.asyncio
async def test_torrent_select_options_sorted_descending_by_seeders(mock_client, mock_config):
    groups = {
        "1080p": [
            _make_torrent_result(filename="low.mkv", seeders=10),
            _make_torrent_result(filename="high.mkv", seeders=500),
            _make_torrent_result(filename="mid.mkv", seeders=200),
        ],
    }
    view = _torrent_view(groups, mock_client, mock_config)
    options = view.select.options
    seeder_order = [int(o.description.split()[0]) for o in options]
    assert seeder_order == sorted(seeder_order, reverse=True)


@pytest.mark.asyncio
async def test_torrent_select_caps_at_configured_limit(mock_client, mock_config):
    mock_config.torrent_results_per_resolution = 3
    groups = {
        "1080p": [_make_torrent_result(seeders=i) for i in range(10)],
    }
    view = _torrent_view(groups, mock_client, mock_config)
    assert len(view.select.options) <= 3


@pytest.mark.asyncio
async def test_torrent_select_groups_all_resolutions(mock_client, mock_config):
    groups = {
        "1080p": [_make_torrent_result(seeders=100)],
        "720p": [_make_torrent_result(seeders=50)],
        "480p": [_make_torrent_result(seeders=20)],
    }
    view = _torrent_view(groups, mock_client, mock_config)
    labels = [o.label for o in view.select.options]
    assert any("1080p" in l for l in labels)
    assert any("720p" in l for l in labels)
    assert any("480p" in l for l in labels)


@pytest.mark.asyncio
async def test_torrent_select_sends_ephemeral_confirm_on_success(mock_client, mock_config):
    groups = {"1080p": [_make_torrent_result(magnet="magnet:?xt=urn:btih:abc")]}
    mock_client.download = AsyncMock(return_value=DownloadResponse(status="success", message="Added."))
    view = _torrent_view(groups, mock_client, mock_config)
    interaction = make_interaction()
    interaction.configure_mock(data={"values": ["1080p:0"]})

    await view.select.callback(interaction)

    interaction.response.defer.assert_awaited_once()
    interaction.followup.send.assert_awaited_once()
    assert interaction.followup.send.call_args.kwargs.get("ephemeral") is True


@pytest.mark.asyncio
async def test_torrent_select_sends_ephemeral_error_on_download_failure(mock_client, mock_config):
    groups = {"1080p": [_make_torrent_result(magnet="magnet:?xt=urn:btih:abc")]}
    mock_client.download = AsyncMock(return_value=None)
    view = _torrent_view(groups, mock_client, mock_config)
    interaction = make_interaction()
    interaction.configure_mock(data={"values": ["1080p:0"]})

    await view.select.callback(interaction)

    interaction.response.defer.assert_awaited_once()
    interaction.followup.send.assert_awaited_once()
    assert interaction.followup.send.call_args.kwargs.get("ephemeral") is True


@pytest.mark.asyncio
async def test_torrent_select_handles_malformed_value(mock_client, mock_config):
    groups = {"1080p": [_make_torrent_result()]}
    view = _torrent_view(groups, mock_client, mock_config)
    interaction = make_interaction()
    interaction.configure_mock(data={"values": ["bad-value"]})

    await view.select.callback(interaction)

    interaction.response.send_message.assert_awaited_once()
    assert interaction.response.send_message.call_args.kwargs.get("ephemeral") is True
