from medialab_contracts import MediaType, TransferInfo

from medialab_bot.embeds import jobs_embed, storage_embed, transfers_embed
from medialab_bot.schemas.jobs import JobsResponse, JobView
from medialab_bot.schemas.system import DiskUsageResponse
from medialab_bot.schemas.transfers import MergedTransfersResponse


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


def _transfers_response(transfers: list[TransferInfo]) -> MergedTransfersResponse:
    return MergedTransfersResponse(
        status="success",
        transfers={"status": "success", "message": "", "data": transfers},
        jobs=[],
    )


def _make_job(**kwargs) -> JobView:
    defaults = {
        "id": 1,
        "torrent_hash": "abc123",
        "release_name": "Dune.2021.1080p",
        "media_type": MediaType.MOVIE,
        "tmdb_id": 438631,
        "status": "DOWNLOADING",
        "created_at": "2026-06-26T00:00:00+00:00",
        "updated_at": "2026-06-26T00:00:00+00:00",
    }
    return JobView(**{**defaults, **kwargs})


# --- transfers_embed ---


def test_transfers_embed_one_field_per_transfer():
    response = _transfers_response([_make_transfer(name=f"Movie{i}.mkv") for i in range(3)])
    embed = transfers_embed(response)
    assert len(embed.fields) == 3


def test_transfers_embed_field_contains_name_and_progress():
    response = _transfers_response([_make_transfer(name="Dune.mkv", progress=0.75)])
    field = transfers_embed(response).fields[0]
    assert "Dune.mkv" in field.name
    assert "75" in (field.value or "") or "75" in field.name


def test_transfers_embed_field_contains_state():
    response = _transfers_response([_make_transfer(state="seeding")])
    field = transfers_embed(response).fields[0]
    assert "seeding" in (field.value or "").lower() or "seeding" in field.name.lower()


# --- jobs_embed ---


def test_jobs_embed_one_field_per_job():
    response = JobsResponse(status="success", jobs=[_make_job(), _make_job(torrent_hash="def")])
    assert len(jobs_embed(response).fields) == 2


def test_jobs_embed_shows_status_and_error():
    response = JobsResponse(
        status="success",
        jobs=[_make_job(status="FAILED", last_error="RENAME: no season")],
    )
    field = jobs_embed(response).fields[0]
    assert "FAILED" in (field.value or "")
    assert "no season" in (field.value or "")


# --- storage_embed ---


def test_storage_embed_contains_free_gb():
    response = DiskUsageResponse(
        status="success",
        path="/media",
        total_gb=2000.0,
        used_gb=800.0,
        free_gb=1200.0,
        used_percent=40.0,
    )
    embed = storage_embed(response)
    combined = " ".join(f.value or "" for f in embed.fields) + (embed.description or "")
    assert "1200" in combined or "1200.0" in combined


def test_storage_embed_contains_used_percent():
    response = DiskUsageResponse(
        status="success",
        path="/media",
        total_gb=2000.0,
        used_gb=800.0,
        free_gb=1200.0,
        used_percent=40.0,
    )
    embed = storage_embed(response)
    combined = " ".join(f.value or "" for f in embed.fields) + (embed.description or "")
    assert "40" in combined
