from medialab_contracts import MediaType

from medialab_bot.client._base import _BaseClient
from medialab_bot.schemas.downloads import DownloadResponse
from medialab_bot.schemas.torrents import TorrentSearchResponse

_DOWNLOAD_ACCEPTED = 202


class _TorrentsMixin(_BaseClient):
    async def search_torrents(
        self,
        query: str,
        media_type: MediaType,
        season: int | None = None,
        episode: int | None = None,
    ) -> TorrentSearchResponse | None:
        params: dict[str, str | int] = {"query": query, "media_type": media_type.value}
        if season is not None:
            params["season"] = season
        if episode is not None:
            params["episode"] = episode
        data = await self._get(
            "/api/v1/search/torrents",
            params=params,
            timeout=self._torrent_search_timeout,
        )
        return self._parse(TorrentSearchResponse, data)

    async def download(
        self, magnet_uri: str, media_type: MediaType, tmdb_id: int
    ) -> DownloadResponse | None:
        # The gateway resolves placement and fans out; it requires media_type +
        # tmdb_id (no title guessing). Save-path config is gone from the bot.
        data = await self._post(
            "/api/v1/download",
            json={
                "magnet_uri": magnet_uri,
                "media_type": media_type.value,
                "tmdb_id": tmdb_id,
            },
            expected_status=_DOWNLOAD_ACCEPTED,
        )
        return self._parse(DownloadResponse, data)
