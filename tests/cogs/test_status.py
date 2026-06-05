import pytest
from unittest.mock import AsyncMock, MagicMock

from medialab_bot.schemas.transfers import TransferInfo, TransferInfoResponse
from medialab_bot.schemas.system import DiskUsage, StorageResponse
from medialab_bot.cogs.status import StatusCog


def _make_transfer(**kwargs) -> TransferInfo:
    defaults = {
        "name": "Dune.2021.mkv",
        "size": 8_000_000_000,
        "progress": 0.45,
        "hash": "abc123",
        "state": "downloading",
        "download_speed": 5_000_000,
        "upload_speed": 0,
        "eta_seconds": 900,
        "save_path": "/media/downloads",
    }
    return TransferInfo(**{**defaults, **kwargs})


def _make_transfers_response(transfers: list[TransferInfo]) -> TransferInfoResponse:
    return TransferInfoResponse(status="success", message="", data=transfers)


def _make_storage_response() -> StorageResponse:
    return StorageResponse(
        status="success",
        message="",
        data=DiskUsage(path="/media", total_gb=2000.0, used_gb=800.0, free_gb=1200.0, used_percent=40.0),
    )


def _make_interaction() -> MagicMock:
    interaction = MagicMock()
    interaction.response = MagicMock()
    interaction.response.defer = AsyncMock()
    interaction.followup = MagicMock()
    interaction.followup.send = AsyncMock()
    return interaction


# --- /transfers ---

@pytest.mark.asyncio
async def test_transfers_defers_before_api_call(mock_client):
    mock_client.get_transfers = AsyncMock(return_value=_make_transfers_response([_make_transfer()]))
    cog = StatusCog(mock_client)
    interaction = _make_interaction()

    await cog.transfers.callback(cog, interaction)

    interaction.response.defer.assert_awaited_once()


@pytest.mark.asyncio
async def test_transfers_sends_embed_on_results(mock_client):
    mock_client.get_transfers = AsyncMock(return_value=_make_transfers_response([_make_transfer()]))
    cog = StatusCog(mock_client)
    interaction = _make_interaction()

    await cog.transfers.callback(cog, interaction)

    interaction.followup.send.assert_awaited_once()
    assert interaction.followup.send.call_args.kwargs.get("embed") is not None


@pytest.mark.asyncio
async def test_transfers_sends_ephemeral_on_empty(mock_client):
    mock_client.get_transfers = AsyncMock(return_value=_make_transfers_response([]))
    cog = StatusCog(mock_client)
    interaction = _make_interaction()

    await cog.transfers.callback(cog, interaction)

    interaction.followup.send.assert_awaited_once()
    assert interaction.followup.send.call_args.kwargs.get("ephemeral") is True


@pytest.mark.asyncio
async def test_transfers_sends_ephemeral_on_client_none(mock_client):
    mock_client.get_transfers = AsyncMock(return_value=None)
    cog = StatusCog(mock_client)
    interaction = _make_interaction()

    await cog.transfers.callback(cog, interaction)

    interaction.followup.send.assert_awaited_once()
    assert interaction.followup.send.call_args.kwargs.get("ephemeral") is True


# --- /storage ---

@pytest.mark.asyncio
async def test_storage_defers_before_api_call(mock_client):
    mock_client.get_storage = AsyncMock(return_value=_make_storage_response())
    cog = StatusCog(mock_client)
    interaction = _make_interaction()

    await cog.storage.callback(cog, interaction)

    interaction.response.defer.assert_awaited_once()


@pytest.mark.asyncio
async def test_storage_sends_embed_on_results(mock_client):
    mock_client.get_storage = AsyncMock(return_value=_make_storage_response())
    cog = StatusCog(mock_client)
    interaction = _make_interaction()

    await cog.storage.callback(cog, interaction)

    interaction.followup.send.assert_awaited_once()
    assert interaction.followup.send.call_args.kwargs.get("embed") is not None


@pytest.mark.asyncio
async def test_storage_sends_ephemeral_on_client_none(mock_client):
    mock_client.get_storage = AsyncMock(return_value=None)
    cog = StatusCog(mock_client)
    interaction = _make_interaction()

    await cog.storage.callback(cog, interaction)

    interaction.followup.send.assert_awaited_once()
    assert interaction.followup.send.call_args.kwargs.get("ephemeral") is True
