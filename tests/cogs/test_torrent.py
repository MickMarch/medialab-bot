import pytest
from unittest.mock import AsyncMock

from medialab_bot.schemas.torrents import TorrentResult, TorrentSearchResponse
from medialab_bot.cogs.torrent import TorrentCog
from tests.helpers import make_interaction


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


@pytest.mark.asyncio
async def test_torrent_defers_before_api_call(mock_client, mock_config):
    mock_client.search_torrents = AsyncMock(
        return_value=_make_torrent_response({"1080p": [_make_torrent_result()]})
    )
    cog = TorrentCog(mock_client, mock_config)
    interaction = make_interaction()

    await cog.torrent.callback(cog, interaction, query="dune")

    interaction.response.defer.assert_awaited_once()


@pytest.mark.asyncio
async def test_torrent_calls_search_torrents_with_query(mock_client, mock_config):
    mock_client.search_torrents = AsyncMock(
        return_value=_make_torrent_response({"1080p": [_make_torrent_result()]})
    )
    cog = TorrentCog(mock_client, mock_config)
    interaction = make_interaction()

    await cog.torrent.callback(cog, interaction, query="dune")

    mock_client.search_torrents.assert_awaited_once_with("dune")


@pytest.mark.asyncio
async def test_torrent_sends_searching_message_then_edits_with_view(mock_client, mock_config):
    mock_client.search_torrents = AsyncMock(
        return_value=_make_torrent_response({"1080p": [_make_torrent_result()]})
    )
    cog = TorrentCog(mock_client, mock_config)
    interaction = make_interaction()

    await cog.torrent.callback(cog, interaction, query="dune")

    interaction.followup.send.assert_awaited_once()
    message = interaction.followup.send.return_value
    message.edit.assert_awaited_once()
    assert message.edit.call_args.kwargs.get("view") is not None


@pytest.mark.asyncio
async def test_torrent_edits_message_with_error_on_empty_results(mock_client, mock_config):
    mock_client.search_torrents = AsyncMock(return_value=_make_torrent_response({}))
    cog = TorrentCog(mock_client, mock_config)
    interaction = make_interaction()

    await cog.torrent.callback(cog, interaction, query="xyzzy")

    message = interaction.followup.send.return_value
    message.edit.assert_awaited_once()


@pytest.mark.asyncio
async def test_torrent_edits_message_with_error_on_client_none(mock_client, mock_config):
    mock_client.search_torrents = AsyncMock(return_value=None)
    cog = TorrentCog(mock_client, mock_config)
    interaction = make_interaction()

    await cog.torrent.callback(cog, interaction, query="dune")

    message = interaction.followup.send.return_value
    message.edit.assert_awaited_once()
