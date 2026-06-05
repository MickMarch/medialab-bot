from medialab_bot.client._base import _BaseClient
from medialab_bot.schemas.downloads import DownloadResponse
from medialab_bot.schemas.torrents import TorrentSearchResponse


class _TorrentsMixin(_BaseClient):
    async def search_torrents(self, query: str) -> TorrentSearchResponse | None:
        data = await self._get("/api/v1/search/torrents", params={"query": query})
        return self._parse(TorrentSearchResponse, data)

    async def download(self, magnet_uri: str) -> DownloadResponse | None:
        data = await self._post(
            "/api/v1/download",
            json={"magnet_uri": magnet_uri, "save_path": self._save_path},
            expected_status=202,
        )
        return self._parse(DownloadResponse, data)
