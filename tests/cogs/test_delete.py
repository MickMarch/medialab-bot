from unittest.mock import AsyncMock, MagicMock

import pytest
from medialab_contracts import MediaType

from medialab_bot.cogs.delete import DeleteCog
from medialab_bot.schemas.deletion import DeletionPlan
from medialab_bot.schemas.jobs import JobsResponse, JobView
from medialab_bot.views.delete import DeleteConfirmView, DeleteSelectView, render_plan
from tests.helpers import make_interaction


def _job(status: str = "DONE", job_id: str = "job-1") -> JobView:
    return JobView(
        id=job_id,
        torrent_hash="abc",
        release_name="Dune.2021.1080p",
        media_type=MediaType.MOVIE,
        tmdb_id=1,
        resolved_title="Dune",
        status=status,
        created_at="2026-06-26T00:00:00+00:00",
        updated_at="2026-06-26T00:00:00+00:00",
    )


def _plan(**kw) -> DeletionPlan:
    base = {
        "status": "success",
        "job_id": "job-1",
        "torrent": False,
        "download_folder": None,
        "placed_paths": ["/media/Movies/Dune (2021)/Dune (2021).mkv"],
        "scan_path": "/media/Movies",
    }
    return DeletionPlan(**{**base, **kw})


async def test_delete_lists_jobs_except_deleted(mock_client):
    mock_client.list_jobs = AsyncMock(
        return_value=JobsResponse(
            status="success", jobs=[_job("DONE", "a"), _job("DELETED", "b"), _job("FAILED", "c")]
        )
    )
    cog = DeleteCog(mock_client)
    interaction = make_interaction()
    await cog.delete.callback(cog, interaction)
    interaction.response.defer.assert_awaited_once_with(ephemeral=True)
    view = interaction.followup.send.await_args.kwargs["view"]
    assert isinstance(view, DeleteSelectView)
    assert [o.value for o in view.select.options] == ["a", "c"]


async def test_delete_says_nothing_to_delete(mock_client):
    mock_client.list_jobs = AsyncMock(return_value=JobsResponse(status="success", jobs=[]))
    cog = DeleteCog(mock_client)
    interaction = make_interaction()
    await cog.delete.callback(cog, interaction)
    assert "Nothing to delete" in interaction.followup.send.await_args.args[0]


async def test_select_shows_plan_with_confirm_button(mock_client):
    mock_client.deletion_plan = AsyncMock(return_value=_plan())
    view = DeleteSelectView(mock_client, [_job()])
    interaction = make_interaction()
    interaction.data = {"values": ["job-1"]}
    await view._on_select(interaction)
    kwargs = interaction.followup.send.await_args.kwargs
    assert "Dune (2021).mkv" in kwargs["content"]
    assert "tell Jellyfin" in kwargs["content"]
    assert isinstance(kwargs["view"], DeleteConfirmView)
    mock_client.delete_job.assert_not_called()


async def test_refused_plan_has_no_confirm_button(mock_client):
    mock_client.deletion_plan = AsyncMock(return_value=_plan(refused="predates tracking; clean /x"))
    view = DeleteSelectView(mock_client, [_job()])
    interaction = make_interaction()
    interaction.data = {"values": ["job-1"]}
    await view._on_select(interaction)
    kwargs = interaction.followup.send.await_args.kwargs
    assert "Cannot delete" in kwargs["content"]
    assert "view" not in kwargs


async def test_confirm_calls_delete_and_reports(mock_client):
    mock_client.delete_job = AsyncMock(return_value=_job("DELETED"))
    view = DeleteConfirmView(mock_client, "job-1")
    interaction = make_interaction()
    await view.confirm.callback(interaction)
    mock_client.delete_job.assert_awaited_once_with("job-1")
    assert "DELETED" in interaction.followup.send.await_args.args[0]


async def test_cancel_does_not_call_delete(mock_client):
    mock_client.delete_job = AsyncMock()
    view = DeleteConfirmView(mock_client, "job-1")
    interaction = make_interaction()
    await view.cancel.callback(interaction)
    mock_client.delete_job.assert_not_called()
    assert "Cancelled" in interaction.response.send_message.await_args.args[0]


def test_render_plan_lists_every_part():
    text = render_plan(_plan(torrent=True, download_folder="/media/Movies/Dune.2021"))
    assert "torrent and its data" in text
    assert "/media/Movies/Dune.2021" in text
    assert "Dune (2021).mkv" in text


def test_render_plan_for_nothing_on_disk():
    text = render_plan(_plan(placed_paths=[], scan_path=None))
    assert "nothing on disk" in text


@pytest.mark.parametrize("n", [16, 40])
def test_render_plan_caps_listed_paths(n):
    text = render_plan(_plan(placed_paths=[f"/p/{i}.mkv" for i in range(n)]))
    assert f"and {n - 15} more" in text


def test_confirm_view_times_out_after_a_minute():
    view = DeleteConfirmView(MagicMock(), "job-1")
    assert view.timeout == 60.0
