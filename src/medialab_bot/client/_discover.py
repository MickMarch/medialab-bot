from medialab_contracts import (
    API_PREFIX,
    DiscoverResponse,
    FollowRequest,
    GenresResponse,
    MediaType,
    WatchlistAddRequest,
    WatchlistItem,
    WatchlistKind,
    WatchlistResponse,
)

from medialab_bot.client._base import _BaseClient

# Follow routes are shows only; the gateway rejects any other media type.
_FOLLOW_MEDIA_TYPE = MediaType.SHOW


class _DiscoverMixin(_BaseClient):
    async def discover(
        self, media_type: MediaType, genre: int | None = None, page: int | None = None
    ) -> DiscoverResponse | None:
        # None covers every failure, TMDB_UNAVAILABLE (503) included.
        params: dict[str, int] = {}
        if genre is not None:
            params["genre"] = genre
        if page is not None:
            params["page"] = page
        data = await self._get(f"{API_PREFIX}/discover/{media_type.value}", params=params)
        return self._parse(DiscoverResponse, data)

    async def discover_genres(self, media_type: MediaType) -> GenresResponse | None:
        data = await self._get(f"{API_PREFIX}/discover/{media_type.value}/genres")
        return self._parse(GenresResponse, data)

    async def list_watchlist(
        self, media_type: MediaType | None = None, kind: WatchlistKind | None = None
    ) -> WatchlistResponse | None:
        params: dict[str, str] = {}
        if media_type is not None:
            params["media_type"] = media_type.value
        if kind is not None:
            params["kind"] = kind.value
        data = await self._get(f"{API_PREFIX}/watchlist", params=params)
        return self._parse(WatchlistResponse, data)

    async def add_to_watchlist(
        self, media_type: MediaType, tmdb_id: int, request: WatchlistAddRequest
    ) -> WatchlistItem | None:
        data = await self._put(
            f"{API_PREFIX}/watchlist/{media_type.value}/{tmdb_id}",
            json=request.model_dump(mode="json"),
        )
        return self._parse(WatchlistItem, data)

    async def remove_from_watchlist(self, media_type: MediaType, tmdb_id: int) -> bool:
        return await self._delete_no_content(f"{API_PREFIX}/watchlist/{media_type.value}/{tmdb_id}")

    async def follow_show(self, tmdb_id: int, request: FollowRequest) -> WatchlistItem | None:
        """The show must already be on the watchlist; the gateway answers 404 otherwise."""
        data = await self._put(
            f"{API_PREFIX}/watchlist/{_FOLLOW_MEDIA_TYPE.value}/{tmdb_id}/follow",
            json=request.model_dump(mode="json"),
        )
        return self._parse(WatchlistItem, data)

    async def unfollow_show(self, tmdb_id: int) -> bool:
        """Back to saved; the row stays."""
        return await self._delete_no_content(
            f"{API_PREFIX}/watchlist/{_FOLLOW_MEDIA_TYPE.value}/{tmdb_id}/follow"
        )
