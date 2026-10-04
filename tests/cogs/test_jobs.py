from unittest.mock import AsyncMock

import pytest
from medialab_contracts import MediaType

from medialab_bot.cogs.jobs import JobsCog
from medialab_bot.schemas.jobs import JobsResponse, JobView
from medialab_bot.views.jobs import JobRetryView
from tests.helpers import make_interaction


def _make_job(status: str = "DOWNLOADING", job_id: str = "job-abc", **kwargs) -> JobView:
    defaults = {
        "id": job_id,
        "torrent_hash": "abc123",
        "release_name": "Dune.2021.1080p",
        "media_type": MediaType.MOVIE,
        "tmdb_id": 438631,
        "status": status,
        "created_at": "2026-06-26T00:00:00+00:00",
        "updated_at": "2026-06-26T00:00:00+00:00",
    }
    return JobView(**{**defaults, **kwargs})


# --- /jobs command ---


@pytest.mark.asyncio
async def test_jobs_defers_before_api_call(mock_client):
    mock_client.list_jobs = AsyncMock(
        return_value=JobsResponse(status="success", jobs=[_make_job()])
    )
    cog = JobsCog(mock_client)
    interaction = make_interaction()

    await cog.jobs.callback(cog, interaction)

    interaction.response.defer.assert_awaited_once()


@pytest.mark.asyncio
async def test_jobs_passes_status_filter(mock_client):
    mock_client.list_jobs = AsyncMock(return_value=JobsResponse(status="success", jobs=[]))
    cog = JobsCog(mock_client)
    interaction = make_interaction()

    await cog.jobs.callback(cog, interaction, status="FAILED")

    mock_client.list_jobs.assert_awaited_once_with(status="FAILED")


@pytest.mark.asyncio
async def test_jobs_sends_embed_on_results(mock_client):
    mock_client.list_jobs = AsyncMock(
        return_value=JobsResponse(status="success", jobs=[_make_job()])
    )
    cog = JobsCog(mock_client)
    interaction = make_interaction()

    await cog.jobs.callback(cog, interaction)

    assert interaction.followup.send.call_args.kwargs.get("embed") is not None


@pytest.mark.asyncio
async def test_jobs_attaches_retry_view_when_failed_present(mock_client):
    mock_client.list_jobs = AsyncMock(
        return_value=JobsResponse(status="success", jobs=[_make_job(status="FAILED")])
    )
    cog = JobsCog(mock_client)
    interaction = make_interaction()

    await cog.jobs.callback(cog, interaction)

    assert isinstance(interaction.followup.send.call_args.kwargs.get("view"), JobRetryView)


@pytest.mark.asyncio
async def test_jobs_omits_view_when_none_failed(mock_client):
    # discord.py rejects view=None; the cog must omit the kwarg entirely when
    # there is no failed job, not pass None. Mirror that contract in the mock so
    # a regression (passing view=None) fails here instead of only at runtime.
    mock_client.list_jobs = AsyncMock(
        return_value=JobsResponse(status="success", jobs=[_make_job(status="DONE")])
    )
    cog = JobsCog(mock_client)
    interaction = make_interaction()

    async def _send(*args, **kwargs):
        if "view" in kwargs and kwargs["view"] is None:
            raise TypeError("expected view parameter to be of type View, not NoneType")

    interaction.followup.send = AsyncMock(side_effect=_send)

    await cog.jobs.callback(cog, interaction)

    assert "view" not in interaction.followup.send.call_args.kwargs


@pytest.mark.asyncio
async def test_jobs_sends_message_on_empty(mock_client):
    mock_client.list_jobs = AsyncMock(return_value=JobsResponse(status="success", jobs=[]))
    cog = JobsCog(mock_client)
    interaction = make_interaction()

    await cog.jobs.callback(cog, interaction)

    interaction.followup.send.assert_awaited_once()


@pytest.mark.asyncio
async def test_jobs_handles_client_none(mock_client):
    mock_client.list_jobs = AsyncMock(return_value=None)
    cog = JobsCog(mock_client)
    interaction = make_interaction()

    await cog.jobs.callback(cog, interaction)

    assert interaction.followup.send.call_args.kwargs.get("ephemeral") is True


# --- JobRetryView ---


@pytest.mark.asyncio
async def test_retry_view_calls_client_retry(mock_client):
    mock_client.retry_job = AsyncMock(return_value=_make_job(status="STOP_SEEDING"))
    view = JobRetryView(mock_client, [_make_job(status="FAILED")])
    interaction = make_interaction()
    interaction.configure_mock(data={"values": ["job-abc"]})

    await view.select.callback(interaction)

    mock_client.retry_job.assert_awaited_once_with("job-abc")
    interaction.followup.send.assert_awaited_once()


@pytest.mark.asyncio
async def test_retry_view_handles_failure(mock_client):
    mock_client.retry_job = AsyncMock(return_value=None)
    view = JobRetryView(mock_client, [_make_job(status="FAILED")])
    interaction = make_interaction()
    interaction.configure_mock(data={"values": ["abc123"]})

    await view.select.callback(interaction)

    assert interaction.followup.send.call_args.kwargs.get("ephemeral") is True


@pytest.mark.asyncio
async def test_jobs_attaches_retry_view_when_needs_attention_present(mock_client):
    mock_client.list_jobs = AsyncMock(
        return_value=JobsResponse(status="success", jobs=[_make_job(status="NEEDS_ATTENTION")])
    )
    cog = JobsCog(mock_client)
    interaction = make_interaction()

    await cog.jobs.callback(cog, interaction)

    kwargs = interaction.followup.send.await_args.kwargs
    assert isinstance(kwargs["view"], JobRetryView)


# --- Dismiss (second select on the same view) ---


@pytest.mark.asyncio
async def test_retry_view_has_a_dismiss_select_too(mock_client):
    view = JobRetryView(mock_client, [_make_job(status="NEEDS_ATTENTION")])
    assert view.dismiss_select in view.children
    assert view.select in view.children
    assert "ismiss" in str(view.dismiss_select.placeholder)


@pytest.mark.asyncio
async def test_dismiss_select_calls_client_dismiss_and_reports_status(mock_client):
    mock_client.dismiss_job = AsyncMock(return_value=_make_job(status="DISMISSED"))
    view = JobRetryView(mock_client, [_make_job(status="NEEDS_ATTENTION")])
    interaction = make_interaction()
    interaction.configure_mock(data={"values": ["job-abc"]})

    await view.dismiss_select.callback(interaction)

    mock_client.dismiss_job.assert_awaited_once_with("job-abc")
    mock_client.retry_job.assert_not_called()
    message = interaction.followup.send.await_args.args[0]
    assert "DISMISSED" in message and "job-abc" in message


@pytest.mark.asyncio
async def test_dismiss_select_handles_failure(mock_client):
    mock_client.dismiss_job = AsyncMock(return_value=None)
    view = JobRetryView(mock_client, [_make_job(status="FAILED")])
    interaction = make_interaction()
    interaction.configure_mock(data={"values": ["job-abc"]})

    await view.dismiss_select.callback(interaction)

    assert interaction.followup.send.call_args.kwargs.get("ephemeral") is True
    assert "failed" in interaction.followup.send.await_args.args[0].lower()


def test_job_view_carries_the_attention_fields():
    job = _make_job(status="NEEDS_ATTENTION", attention_cause="TORRENT_GONE", dismissed_at=None)
    assert job.attention_cause == "TORRENT_GONE"
    assert job.dismissed_at is None
