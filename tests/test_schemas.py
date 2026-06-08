from medialab_bot.schemas.downloads import DownloadResponse
from medialab_bot.schemas.errors import ErrorResponse
from medialab_bot.schemas.system import DiskUsageResponse, HealthResponse
from medialab_bot.schemas.tmdb import (
    TmdbMediaDetailResponse,
    TmdbSearchResponse,
    TmdbSearchResult,
)
from medialab_bot.schemas.torrents import TorrentResult, TorrentSearchResponse
from medialab_bot.schemas.transfers import TransferInfo, TransferInfoResponse

# --- system ---


def test_health_response_parses():
    data = {"status": "online", "uptime_seconds": 123.45, "vpn_interface_bound": True}
    model = HealthResponse(**data)
    assert model.status == "online"
    assert model.uptime_seconds == 123.45
    assert model.vpn_interface_bound is True


def test_health_response_vpn_false():
    data = {"status": "online", "uptime_seconds": 0.0, "vpn_interface_bound": False}
    model = HealthResponse(**data)
    assert model.vpn_interface_bound is False


def test_storage_response_parses():
    data = {
        "status": "success",
        "path": "/media",
        "total_gb": 2000.0,
        "used_gb": 800.0,
        "free_gb": 1200.0,
        "used_percent": 40.0,
    }
    response = DiskUsageResponse(**data)
    assert response.free_gb == 1200.0


# --- tmdb ---


def test_tmdb_search_result_parses():
    data = {
        "tmdb_id": 123,
        "title": "Dune",
        "year": "2021",
        "media_type": "movie",
        "overview": "A desert planet.",
        "vote_average": 7.9,
        "poster_path": "/abc.jpg",
    }
    result = TmdbSearchResult(**data)
    assert result.tmdb_id == 123
    assert result.title == "Dune"
    assert result.poster_path == "/abc.jpg"


def test_tmdb_search_result_null_poster():
    data = {
        "tmdb_id": 1,
        "title": "No Poster",
        "year": "2020",
        "media_type": "tv",
        "overview": "",
        "vote_average": 0.0,
        "poster_path": None,
    }
    result = TmdbSearchResult(**data)
    assert result.poster_path is None


def test_tmdb_search_response_parses():
    data = {
        "status": "success",
        "message": "",
        "data": [
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
    }
    response = TmdbSearchResponse(**data)
    assert len(response.data) == 1
    assert response.data[0].title == "Movie A"


def test_tmdb_media_detail_response_parses_with_data():
    data = {
        "status": "success",
        "message": "",
        "data": {"title": "Dune", "tmdb_id": 438631},
    }
    response = TmdbMediaDetailResponse(**data)
    assert response.data["title"] == "Dune"


def test_tmdb_media_detail_response_parses_null_data():
    data = {"status": "success", "message": "", "data": None}
    response = TmdbMediaDetailResponse(**data)
    assert response.data is None


# --- torrents ---


def test_torrent_result_parses():
    data = {
        "fileName": "Dune.2021.1080p.BluRay.mkv",
        "fileUrl": "magnet:?xt=urn:btih:abc123",
        "nbSeeders": 150,
        "nbLeechers": 10,
        "fileSize": 10_000_000_000,
    }
    result = TorrentResult(**data)
    assert result.file_name == "Dune.2021.1080p.BluRay.mkv"
    assert result.seeders == 150
    assert result.file_size == 10_000_000_000


def test_torrent_search_response_parses_grouped_by_resolution():
    data = {
        "status": "success",
        "message": "",
        "data": {
            "1080p": [
                {
                    "fileName": "Dune.1080p.mkv",
                    "fileUrl": "magnet:?xt=urn:btih:abc",
                    "nbSeeders": 100,
                    "nbLeechers": 5,
                    "fileSize": 8_000_000_000,
                }
            ],
            "720p": [
                {
                    "fileName": "Dune.720p.mkv",
                    "fileUrl": "magnet:?xt=urn:btih:def",
                    "nbSeeders": 50,
                    "nbLeechers": 2,
                    "fileSize": 4_000_000_000,
                }
            ],
        },
    }
    response = TorrentSearchResponse(**data)
    assert "1080p" in response.data
    assert len(response.data["1080p"]) == 1
    assert response.data["1080p"][0].file_name == "Dune.1080p.mkv"


def test_torrent_search_response_parses_empty_data():
    data = {"status": "success", "message": "No results.", "data": {}}
    response = TorrentSearchResponse(**data)
    assert response.data == {}


# --- transfers ---


def test_transfer_info_parses():
    data = {
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
    info = TransferInfo(**data)
    assert info.name == "Dune.2021.mkv"
    assert info.progress == 0.45
    assert info.state == "downloading"


def test_transfer_info_response_parses():
    transfer = {
        "name": "Movie.mkv",
        "size": 1_000_000,
        "progress": 1.0,
        "hash": "deadbeef",
        "state": "seeding",
        "download_speed": 0,
        "upload_speed": 1_000,
        "eta_seconds": 0,
        "save_path": "/media/downloads",
    }
    data = {"status": "success", "message": "", "data": [transfer]}
    response = TransferInfoResponse(**data)
    assert len(response.data) == 1
    assert response.data[0].state == "seeding"


def test_transfer_info_response_empty():
    data = {"status": "success", "message": "", "data": []}
    response = TransferInfoResponse(**data)
    assert response.data == []


# --- downloads ---


def test_download_response_parses():
    resp = DownloadResponse(status="success", message="Torrent added.")
    assert resp.status == "success"


# --- errors ---


def test_error_response_parses():
    data = {"status": "error", "code": "UNAUTHORIZED", "detail": "Missing API key."}
    err = ErrorResponse(**data)
    assert err.code == "UNAUTHORIZED"
    assert err.status == "error"
