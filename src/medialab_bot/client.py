from typing import Self

import httpx
from pydantic import ValidationError

from medialab_bot.schemas.system import HealthResponse
from medialab_bot.schemas.tmdb import TmdbSearchResponse


class TorrentDownloaderClient:
    def __init__(self, base_url: str, api_key: str) -> None:
        self._http = httpx.AsyncClient(
            base_url=base_url,
            headers={"X-API-Key": api_key},
        )

    async def health(self) -> HealthResponse | None:
        try:
            response = await self._http.get("/api/v1/health")
            if response.status_code != 200:
                return None
            return HealthResponse(**response.json())
        except (httpx.ConnectError, httpx.HTTPError, ValidationError, ValueError):
            return None

    async def search_tmdb(self, query: str) -> TmdbSearchResponse | None:
        try:
            response = await self._http.get("/api/v1/search/tmdb", params={"query": query})
            if response.status_code != 200:
                return None
            return TmdbSearchResponse(**response.json())
        except (httpx.ConnectError, httpx.HTTPError, ValidationError, ValueError):
            return None

    async def close(self) -> None:
        await self._http.aclose()

    async def __aenter__(self) -> Self:
        return self

    async def __aexit__(self, *_) -> None:
        await self.close()
