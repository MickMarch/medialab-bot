from medialab_contracts import MediaType

from medialab_bot.schemas.downloads import DownloadResponse
from medialab_bot.schemas.jobs import JobsResponse, JobView
from medialab_bot.schemas.system import DiskUsageResponse, HealthResponse
from medialab_bot.schemas.tmdb import (
    TmdbMediaDetailResponse,
    TmdbSearchResponse,
    TmdbSearchResult,
)
from medialab_bot.schemas.torrents import TorrentResult, TorrentSearchResponse
from medialab_bot.schemas.transfers import MergedTransfersResponse

# Shared models (MediaType, ErrorResponse, TransferInfo) are owned and tested by
# medialab-contracts; the bot does not re-test their parsing here.

_JOB = {
    "id": 1,
    "torrent_hash": "abc123",
    "release_name": "Dune.2021.1080p",
    "media_type": "movie",
    "tmdb_id": 438631,
    "status": "DONE",
    "created_at": "2026-06-26T00:00:00+00:00",
    "updated_at": "2026-06-26T00:00:00+00:00",
}


# --- system (aggregated health) ---


def test_health_response_parses_downstream():
    model = HealthResponse(
        status="online",
        uptime_seconds=123.45,
        downstream={"torrent_downloader": True, "medialab_jellyfin": False},
    )
    assert model.downstream.torrent_downloader is True
    assert model.downstream.medialab_jellyfin is False


def test_storage_response_parses():
    response = DiskUsageResponse(
        status="success",
        path="/media",
        total_gb=2000.0,
        used_gb=800.0,
        free_gb=1200.0,
        used_percent=40.0,
    )
    assert response.free_gb == 1200.0


# --- tmdb ---


def test_tmdb_search_result_parses():
    result = TmdbSearchResult(
        tmdb_id=123,
        title="Dune",
        year="2021",
        media_type="movie",
        overview="A desert planet.",
        vote_average=7.9,
        poster_path="/abc.jpg",
    )
    assert result.tmdb_id == 123
    assert result.poster_path == "/abc.jpg"


def test_tmdb_search_response_parses():
    response = TmdbSearchResponse(
        status="success",
        message="",
        data=[
            {
                "tmdb_id": 1,
                "title": "Movie A",
                "year": "2022",
                "media_type": "movie",
                "overview": "Overview.",
                "vote_average": 6.5,
                "poster_path": None,
            }
        ],
    )
    assert response.data[0].title == "Movie A"


def test_tmdb_media_detail_response_parses_null_data():
    response = TmdbMediaDetailResponse(status="success", message="", data=None)
    assert response.data is None


# --- torrents ---


def test_torrent_result_parses():
    result = TorrentResult(
        fileName="Dune.2021.1080p.BluRay.mkv",
        fileUrl="magnet:?xt=urn:btih:abc123",
        nbSeeders=150,
        nbLeechers=10,
        fileSize=10_000_000_000,
    )
    assert result.file_name == "Dune.2021.1080p.BluRay.mkv"
    assert result.seeders == 150


def test_torrent_search_response_groups_by_resolution():
    response = TorrentSearchResponse(
        status="success",
        message="",
        data={
            "1080p": [
                {
                    "fileName": "Dune.1080p.mkv",
                    "fileUrl": "magnet:?xt=urn:btih:abc",
                    "nbSeeders": 100,
                    "nbLeechers": 5,
                    "fileSize": 8_000_000_000,
                }
            ]
        },
    )
    assert response.data["1080p"][0].file_name == "Dune.1080p.mkv"


# --- jobs ---


def test_job_view_parses_with_media_type_enum():
    job = JobView(**_JOB)
    assert job.media_type is MediaType.MOVIE
    assert job.status == "DONE"
    assert job.attempts == 0


def test_jobs_response_parses():
    response = JobsResponse(status="success", jobs=[_JOB])
    assert len(response.jobs) == 1


# --- transfers (merged) ---


def test_merged_transfers_response_parses():
    response = MergedTransfersResponse(
        status="success",
        transfers={"status": "success", "message": "", "data": []},
        jobs=[_JOB],
    )
    assert response.transfers.data == []
    assert len(response.jobs) == 1


# --- downloads ---


def test_download_response_wraps_job():
    response = DownloadResponse(status="success", job=_JOB)
    assert response.job.torrent_hash == "abc123"
