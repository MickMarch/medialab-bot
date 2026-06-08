from medialab_bot.client._base import _BaseClient
from medialab_bot.schemas.tmdb import TmdbMediaDetailResponse, TmdbSearchResponse


class _TmdbMixin(_BaseClient):
    async def search_tmdb(self, query: str) -> TmdbSearchResponse | None:
        data = await self._get("/api/v1/search/tmdb", params={"query": query})
        return self._parse(TmdbSearchResponse, data)

    async def search_tmdb_movie(self, tmdb_id: int) -> TmdbMediaDetailResponse | None:
        data = await self._get(f"/api/v1/search/tmdb/movie/{tmdb_id}")
        return self._parse(TmdbMediaDetailResponse, data)

    async def search_tmdb_show(self, tmdb_id: int) -> TmdbMediaDetailResponse | None:
        data = await self._get(f"/api/v1/search/tmdb/show/{tmdb_id}")
        return self._parse(TmdbMediaDetailResponse, data)
