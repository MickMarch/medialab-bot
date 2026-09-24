from unittest.mock import AsyncMock

import pytest
from medialab_contracts import TransferInfo

from medialab_bot.cogs.status import StatusCog
from medialab_bot.schemas.actions import ActionResponse
from medialab_bot.schemas.system import DiskUsageResponse
from medialab_bot.schemas.transfers import MergedTransfersResponse
from tests.helpers import make_interaction


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


def _make_transfers_response(transfers: list[TransferInfo]) -> MergedTransfersResponse:
    return MergedTransfersResponse(
        status="success",
        transfers={"status": "success", "message": "", "data": transfers},
        jobs=[],
    )


def _make_storage_response() -> DiskUsageResponse:
    return DiskUsageResponse(
        status="success",
        path="/media",
        total_gb=2000.0,
        used_gb=800.0,
        free_gb=1200.0,
        used_percent=40.0,
    )


# --- /transfers ---


@pytest.mark.asyncio
async def test_transfers_defers_before_api_call(mock_client):
    mock_client.get_transfers = AsyncMock(return_value=_make_transfers_response([_make_transfer()]))
    cog = StatusCog(mock_client)
    interaction = make_interaction()

    await cog.transfers.callback(cog, interaction)

    interaction.response.defer.assert_awaited_once()


@pytest.mark.asyncio
async def test_transfers_sends_embed_on_results(mock_client):
    mock_client.get_transfers = AsyncMock(return_value=_make_transfers_response([_make_transfer()]))
    cog = StatusCog(mock_client)
    interaction = make_interaction()

    await cog.transfers.callback(cog, interaction)

    interaction.followup.send.assert_awaited_once()
    assert interaction.followup.send.call_args.kwargs.get("embed") is not None


@pytest.mark.asyncio
async def test_transfers_sends_ephemeral_on_empty(mock_client):
    mock_client.get_transfers = AsyncMock(return_value=_make_transfers_response([]))
    cog = StatusCog(mock_client)
    interaction = make_interaction()

    await cog.transfers.callback(cog, interaction)

    interaction.followup.send.assert_awaited_once()
    assert interaction.followup.send.call_args.kwargs.get("ephemeral") is True


@pytest.mark.asyncio
async def test_transfers_sends_ephemeral_on_client_none(mock_client):
    mock_client.get_transfers = AsyncMock(return_value=None)
    cog = StatusCog(mock_client)
    interaction = make_interaction()

    await cog.transfers.callback(cog, interaction)

    interaction.followup.send.assert_awaited_once()
    assert interaction.followup.send.call_args.kwargs.get("ephemeral") is True


# --- /storage ---


@pytest.mark.asyncio
async def test_storage_defers_before_api_call(mock_client):
    mock_client.get_storage = AsyncMock(return_value=_make_storage_response())
    cog = StatusCog(mock_client)
    interaction = make_interaction()

    await cog.storage.callback(cog, interaction)

    interaction.response.defer.assert_awaited_once()


@pytest.mark.asyncio
async def test_storage_sends_embed_on_results(mock_client):
    mock_client.get_storage = AsyncMock(return_value=_make_storage_response())
    cog = StatusCog(mock_client)
    interaction = make_interaction()

    await cog.storage.callback(cog, interaction)

    interaction.followup.send.assert_awaited_once()
    assert interaction.followup.send.call_args.kwargs.get("embed") is not None


@pytest.mark.asyncio
async def test_storage_sends_ephemeral_on_client_none(mock_client):
    mock_client.get_storage = AsyncMock(return_value=None)
    cog = StatusCog(mock_client)
    interaction = make_interaction()

    await cog.storage.callback(cog, interaction)

    interaction.followup.send.assert_awaited_once()
    assert interaction.followup.send.call_args.kwargs.get("ephemeral") is True


# --- /stop-seeding ---


@pytest.mark.asyncio
async def test_stop_seeding_defers_before_api_call(mock_client):
    mock_client.stop_seeding = AsyncMock(
        return_value=ActionResponse(status="success", message="All seeding transfers stopped.")
    )
    cog = StatusCog(mock_client)
    interaction = make_interaction()

    await cog.stop_seeding.callback(cog, interaction)

    interaction.response.defer.assert_awaited_once_with(ephemeral=True)
    mock_client.stop_seeding.assert_awaited_once()


@pytest.mark.asyncio
async def test_stop_seeding_reports_the_gateway_message(mock_client):
    mock_client.stop_seeding = AsyncMock(
        return_value=ActionResponse(status="success", message="All seeding transfers stopped.")
    )
    cog = StatusCog(mock_client)
    interaction = make_interaction()

    await cog.stop_seeding.callback(cog, interaction)

    sent = interaction.followup.send.await_args
    assert "All seeding transfers stopped." in sent.args[0]
    assert sent.kwargs["ephemeral"] is True


@pytest.mark.asyncio
async def test_stop_seeding_sends_failure_line_on_client_none(mock_client):
    mock_client.stop_seeding = AsyncMock(return_value=None)
    cog = StatusCog(mock_client)
    interaction = make_interaction()

    await cog.stop_seeding.callback(cog, interaction)

    sent = interaction.followup.send.await_args
    assert "Failed" in sent.args[0]
    assert sent.kwargs["ephemeral"] is True
