import pytest
import httpx
from unittest.mock import AsyncMock, MagicMock, patch

from medialab_bot.client import TorrentDownloaderClient
from medialab_bot.schemas.system import HealthResponse
from medialab_bot.schemas.tmdb import TmdbSearchResponse

BASE_URL = "http://localhost:8000"
API_KEY = "test-key"


@pytest.fixture
def client():
    return TorrentDownloaderClient(base_url=BASE_URL, api_key=API_KEY)


@pytest.mark.asyncio
async def test_health_returns_response_on_200(client):
    payload = {"status": "online", "uptime_seconds": 55.0, "vpn_interface_bound": True}
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = payload

    with patch.object(client._http, "get", new=AsyncMock(return_value=mock_response)):
        result = await client.health()

    assert isinstance(result, HealthResponse)
    assert result.status == "online"
    assert result.vpn_interface_bound is True


@pytest.mark.asyncio
async def test_health_returns_none_on_non_200(client):
    mock_response = MagicMock()
    mock_response.status_code = 503

    with patch.object(client._http, "get", new=AsyncMock(return_value=mock_response)):
        result = await client.health()

    assert result is None


@pytest.mark.asyncio
async def test_health_returns_none_on_connect_error(client):
    with patch.object(client._http, "get", new=AsyncMock(side_effect=httpx.ConnectError("refused"))):
        result = await client.health()

    assert result is None


@pytest.mark.asyncio
async def test_api_key_header_sent(client):
    payload = {"status": "online", "uptime_seconds": 1.0, "vpn_interface_bound": False}
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = payload

    with patch.object(client._http, "get", new=AsyncMock(return_value=mock_response)) as mock_get:
        await client.health()

    mock_get.assert_called_once()
    _, kwargs = mock_get.call_args
    assert kwargs.get("headers", {}).get("X-API-Key") == API_KEY or \
        client._http.headers.get("X-API-Key") == API_KEY


@pytest.mark.asyncio
async def test_context_manager_closes_client():
    async with TorrentDownloaderClient(base_url=BASE_URL, api_key=API_KEY) as client:
        assert client is not None

    assert client._http.is_closed


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
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = payload

    with patch.object(client._http, "get", new=AsyncMock(return_value=mock_response)):
        result = await client.search_tmdb("dune")

    assert isinstance(result, TmdbSearchResponse)
    assert len(result.data) == 1
    assert result.data[0].title == "Dune"


@pytest.mark.asyncio
async def test_search_tmdb_returns_none_on_non_200(client):
    mock_response = MagicMock()
    mock_response.status_code = 429

    with patch.object(client._http, "get", new=AsyncMock(return_value=mock_response)):
        result = await client.search_tmdb("dune")

    assert result is None


@pytest.mark.asyncio
async def test_search_tmdb_returns_none_on_connect_error(client):
    with patch.object(client._http, "get", new=AsyncMock(side_effect=httpx.ConnectError("refused"))):
        result = await client.search_tmdb("dune")

    assert result is None
