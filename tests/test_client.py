from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from medialab_bot.client import TorrentDownloaderClient
from medialab_bot.schemas.downloads import DownloadResponse
from medialab_bot.schemas.system import DiskUsageResponse, HealthResponse
from medialab_bot.schemas.tmdb import TmdbMediaDetailResponse, TmdbSearchResponse
from medialab_bot.schemas.torrents import TorrentSearchResponse
from medialab_bot.schemas.transfers import TransferInfoResponse

BASE_URL = "http://localhost:8000"
API_KEY = "test-key"
SAVE_PATH = "/media/downloads"
TMP_DOCKER_SAVE_PATH = "/tmp/downloads"


@pytest.fixture
def client():
    return TorrentDownloaderClient(
        base_url=BASE_URL,
        api_key=API_KEY,
        save_path=SAVE_PATH,
        tmp_docker_save_path=TMP_DOCKER_SAVE_PATH,
    )


def _mock_response(status_code: int, payload: dict | None = None) -> MagicMock:
    r = MagicMock()
    r.status_code = status_code
    if payload is not None:
        r.json.return_value = payload
    return r


# --- infrastructure ---


@pytest.mark.asyncio
async def test_api_key_set_in_headers(client):
    assert client._http.headers.get("x-api-key") == API_KEY


@pytest.mark.asyncio
async def test_context_manager_closes_client():
    async with TorrentDownloaderClient(
        base_url=BASE_URL,
        api_key=API_KEY,
        save_path=SAVE_PATH,
        tmp_docker_save_path=TMP_DOCKER_SAVE_PATH,
    ) as c:
        assert c is not None
    assert c._http.is_closed


# --- health ---


@pytest.mark.asyncio
async def test_health_returns_response_on_200(client):
    payload = {"status": "online", "uptime_seconds": 55.0, "vpn_interface_bound": True}
    with patch.object(
        client._http, "get", new=AsyncMock(return_value=_mock_response(200, payload))
    ):
        result = await client.health()
    assert isinstance(result, HealthResponse)
    assert result.status == "online"


@pytest.mark.asyncio
async def test_health_returns_none_on_non_200(client):
    with patch.object(client._http, "get", new=AsyncMock(return_value=_mock_response(503))):
        result = await client.health()
    assert result is None


@pytest.mark.asyncio
async def test_health_returns_none_on_connect_error(client):
    with patch.object(
        client._http, "get", new=AsyncMock(side_effect=httpx.ConnectError("refused"))
    ):
        result = await client.health()
    assert result is None


@pytest.mark.asyncio
async def test_health_returns_none_on_bad_json(client):
    r = _mock_response(200)
    r.json.side_effect = ValueError("bad json")
    with patch.object(client._http, "get", new=AsyncMock(return_value=r)):
        result = await client.health()
    assert result is None


# --- search_tmdb ---


@pytest.mark.asyncio
async def test_search_tmdb_returns_response_on_200(client):
    payload = {
        "status": "success",
        "message": "",
        "data": [
            {
                "tmdb_id": 1,
                "title": "Dune",
                "year": "2021",
                "media_type": "movie",
                "overview": "Desert planet.",
                "vote_average": 7.9,
                "poster_path": None,
            }
        ],
    }
    with patch.object(
        client._http, "get", new=AsyncMock(return_value=_mock_response(200, payload))
    ):
        result = await client.search_tmdb("dune")
    assert isinstance(result, TmdbSearchResponse)
    assert result.data[0].title == "Dune"


@pytest.mark.asyncio
async def test_search_tmdb_returns_none_on_non_200(client):
    with patch.object(client._http, "get", new=AsyncMock(return_value=_mock_response(429))):
        result = await client.search_tmdb("dune")
    assert result is None


@pytest.mark.asyncio
async def test_search_tmdb_returns_none_on_connect_error(client):
    with patch.object(
        client._http, "get", new=AsyncMock(side_effect=httpx.ConnectError("refused"))
    ):
        result = await client.search_tmdb("dune")
    assert result is None


@pytest.mark.asyncio
async def test_search_tmdb_returns_none_on_bad_json(client):
    r = _mock_response(200)
    r.json.side_effect = ValueError("bad json")
    with patch.object(client._http, "get", new=AsyncMock(return_value=r)):
        result = await client.search_tmdb("dune")
    assert result is None


# --- search_tmdb_movie ---


@pytest.mark.asyncio
async def test_search_tmdb_movie_returns_response_on_200(client):
    payload = {
        "status": "success",
        "message": "",
        "data": {"title": "Dune", "tmdb_id": 438631},
    }
    with patch.object(
        client._http, "get", new=AsyncMock(return_value=_mock_response(200, payload))
    ):
        result = await client.search_tmdb_movie(438631)
    assert isinstance(result, TmdbMediaDetailResponse)
    assert result.data["title"] == "Dune"


@pytest.mark.asyncio
async def test_search_tmdb_movie_calls_correct_path(client):
    payload = {"status": "success", "message": "", "data": {}}
    mock_get = AsyncMock(return_value=_mock_response(200, payload))
    with patch.object(client._http, "get", new=mock_get):
        await client.search_tmdb_movie(438631)
    mock_get.assert_awaited_once()
    assert "/api/v1/search/tmdb/movie/438631" in mock_get.call_args.args[0]


@pytest.mark.asyncio
async def test_search_tmdb_movie_returns_none_on_non_200(client):
    with patch.object(client._http, "get", new=AsyncMock(return_value=_mock_response(404))):
        result = await client.search_tmdb_movie(999)
    assert result is None


@pytest.mark.asyncio
async def test_search_tmdb_movie_returns_none_on_connect_error(client):
    with patch.object(
        client._http, "get", new=AsyncMock(side_effect=httpx.ConnectError("refused"))
    ):
        result = await client.search_tmdb_movie(438631)
    assert result is None


# --- search_tmdb_show ---


@pytest.mark.asyncio
async def test_search_tmdb_show_returns_response_on_200(client):
    payload = {
        "status": "success",
        "message": "",
        "data": {"name": "Breaking Bad", "tmdb_id": 1396},
    }
    with patch.object(
        client._http, "get", new=AsyncMock(return_value=_mock_response(200, payload))
    ):
        result = await client.search_tmdb_show(1396)
    assert isinstance(result, TmdbMediaDetailResponse)
    assert result.data["name"] == "Breaking Bad"


@pytest.mark.asyncio
async def test_search_tmdb_show_calls_correct_path(client):
    payload = {"status": "success", "message": "", "data": {}}
    mock_get = AsyncMock(return_value=_mock_response(200, payload))
    with patch.object(client._http, "get", new=mock_get):
        await client.search_tmdb_show(1396)
    mock_get.assert_awaited_once()
    assert "/api/v1/search/tmdb/show/1396" in mock_get.call_args.args[0]


@pytest.mark.asyncio
async def test_search_tmdb_show_returns_none_on_non_200(client):
    with patch.object(client._http, "get", new=AsyncMock(return_value=_mock_response(404))):
        result = await client.search_tmdb_show(999)
    assert result is None


# --- search_torrents ---


@pytest.mark.asyncio
async def test_search_torrents_returns_response_on_200(client):
    payload = {
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
            ]
        },
    }
    with patch.object(
        client._http, "get", new=AsyncMock(return_value=_mock_response(200, payload))
    ):
        result = await client.search_torrents("dune")
    assert isinstance(result, TorrentSearchResponse)
    assert "1080p" in result.data


@pytest.mark.asyncio
async def test_search_torrents_passes_query_param(client):
    payload = {"status": "success", "message": "", "data": {}}
    mock_get = AsyncMock(return_value=_mock_response(200, payload))
    with patch.object(client._http, "get", new=mock_get):
        await client.search_torrents("dune")
    _, kwargs = mock_get.call_args
    assert kwargs.get("params", {}).get("query") == "dune"


@pytest.mark.asyncio
async def test_search_torrents_returns_none_on_non_200(client):
    with patch.object(client._http, "get", new=AsyncMock(return_value=_mock_response(429))):
        result = await client.search_torrents("dune")
    assert result is None


@pytest.mark.asyncio
async def test_search_torrents_returns_none_on_connect_error(client):
    with patch.object(
        client._http, "get", new=AsyncMock(side_effect=httpx.ConnectError("refused"))
    ):
        result = await client.search_torrents("dune")
    assert result is None


# --- download ---


@pytest.mark.asyncio
async def test_download_returns_response_on_202(client):
    payload = {"status": "success", "message": "Torrent added to queue."}
    with patch.object(
        client._http, "post", new=AsyncMock(return_value=_mock_response(202, payload))
    ):
        result = await client.download("magnet:?xt=urn:btih:abc")
    assert isinstance(result, DownloadResponse)
    assert result.status == "success"


@pytest.mark.asyncio
async def test_download_sends_save_path_from_config(client):
    payload = {"status": "success", "message": "Torrent added."}
    mock_post = AsyncMock(return_value=_mock_response(202, payload))
    with patch.object(client._http, "post", new=mock_post):
        await client.download("magnet:?xt=urn:btih:abc")
    _, kwargs = mock_post.call_args
    body = kwargs.get("json", {})
    assert body.get("save_path") == SAVE_PATH
    assert body.get("magnet_uri") == "magnet:?xt=urn:btih:abc"


@pytest.mark.asyncio
async def test_download_returns_none_on_non_202(client):
    with patch.object(client._http, "post", new=AsyncMock(return_value=_mock_response(503))):
        result = await client.download("magnet:?xt=urn:btih:abc")
    assert result is None


@pytest.mark.asyncio
async def test_download_returns_none_on_connect_error(client):
    with patch.object(
        client._http, "post", new=AsyncMock(side_effect=httpx.ConnectError("refused"))
    ):
        result = await client.download("magnet:?xt=urn:btih:abc")
    assert result is None


# --- get_transfers ---


@pytest.mark.asyncio
async def test_get_transfers_returns_response_on_200(client):
    payload = {
        "status": "success",
        "message": "",
        "data": [
            {
                "name": "Movie.mkv",
                "size": 1_000_000,
                "progress": 0.5,
                "hash": "abc",
                "state": "downloading",
                "download_speed": 1_000_000,
                "upload_speed": 0,
                "eta_seconds": 600,
                "save_path": "/media/downloads",
            }
        ],
    }
    with patch.object(
        client._http, "get", new=AsyncMock(return_value=_mock_response(200, payload))
    ):
        result = await client.get_transfers()
    assert isinstance(result, TransferInfoResponse)
    assert len(result.data) == 1


@pytest.mark.asyncio
async def test_get_transfers_returns_none_on_non_200(client):
    with patch.object(client._http, "get", new=AsyncMock(return_value=_mock_response(503))):
        result = await client.get_transfers()
    assert result is None


@pytest.mark.asyncio
async def test_get_transfers_returns_none_on_connect_error(client):
    with patch.object(
        client._http, "get", new=AsyncMock(side_effect=httpx.ConnectError("refused"))
    ):
        result = await client.get_transfers()
    assert result is None


# --- get_storage ---


@pytest.mark.asyncio
async def test_get_storage_returns_response_on_200(client):
    payload = {
        "status": "success",
        "path": "/media",
        "total_gb": 2000.0,
        "used_gb": 800.0,
        "free_gb": 1200.0,
        "used_percent": 40.0,
    }
    with patch.object(
        client._http, "get", new=AsyncMock(return_value=_mock_response(200, payload))
    ):
        result = await client.get_storage()
    assert isinstance(result, DiskUsageResponse)
    assert result.free_gb == 1200.0


@pytest.mark.asyncio
async def test_get_storage_returns_none_on_non_200(client):
    with patch.object(client._http, "get", new=AsyncMock(return_value=_mock_response(503))):
        result = await client.get_storage()
    assert result is None


@pytest.mark.asyncio
async def test_get_storage_returns_none_on_connect_error(client):
    with patch.object(
        client._http, "get", new=AsyncMock(side_effect=httpx.ConnectError("refused"))
    ):
        result = await client.get_storage()
    assert result is None
