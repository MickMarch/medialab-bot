from medialab_bot.client._base import _BaseClient
from medialab_bot.schemas.system import DiskUsageResponse, HealthResponse
from medialab_bot.schemas.transfers import MergedTransfersResponse


class _StatusMixin(_BaseClient):
    async def health(self) -> HealthResponse | None:
        data = await self._get("/api/v1/health")
        return self._parse(HealthResponse, data)

    async def get_transfers(self) -> MergedTransfersResponse | None:
        data = await self._get("/api/v1/transfers")
        return self._parse(MergedTransfersResponse, data)

    async def get_storage(self) -> DiskUsageResponse | None:
        # The gateway resolves the storage path itself; no path arg from the bot.
        data = await self._get("/api/v1/storage")
        return self._parse(DiskUsageResponse, data)
