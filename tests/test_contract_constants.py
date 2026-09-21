"""The client builds every gateway path from the shared prefix and sends the shared header."""

from unittest.mock import AsyncMock

import pytest
from medialab_contracts import API_KEY_HEADER, API_PREFIX, MediaType

from medialab_bot.client import OrchestratorClient


@pytest.fixture
def client() -> OrchestratorClient:
    return OrchestratorClient(base_url="http://gateway", api_key="k")


def test_sends_the_shared_api_key_header(client: OrchestratorClient) -> None:
    assert client._http.headers[API_KEY_HEADER] == "k"


@pytest.mark.parametrize(
    ("call", "expected"),
    [
        (lambda c: c.health(), "/health"),
        (lambda c: c.get_transfers(), "/transfers"),
        (lambda c: c.get_storage(), "/storage"),
        (lambda c: c.list_jobs(), "/jobs"),
        (lambda c: c.search_tmdb("x"), "/search/tmdb"),
        (lambda c: c.search_tmdb_movie(1), f"/search/tmdb/{MediaType.MOVIE.value}/1"),
        (lambda c: c.search_tmdb_show(2), f"/search/tmdb/{MediaType.SHOW.value}/2"),
        (lambda c: c.search_torrents("x", MediaType.MOVIE), "/search/torrents"),
    ],
)
async def test_get_paths_are_built_from_the_shared_prefix(client, call, expected) -> None:
    client._get = AsyncMock(return_value=None)
    await call(client)
    assert client._get.call_args.args[0] == f"{API_PREFIX}{expected}"


@pytest.mark.parametrize(
    ("call", "expected"),
    [
        (lambda c: c.retry_job("j1"), "/jobs/j1/retry"),
        (lambda c: c.download("magnet:?x", MediaType.SHOW, 5), "/download"),
    ],
)
async def test_post_paths_are_built_from_the_shared_prefix(client, call, expected) -> None:
    client._post = AsyncMock(return_value=None)
    await call(client)
    assert client._post.call_args.args[0] == f"{API_PREFIX}{expected}"
