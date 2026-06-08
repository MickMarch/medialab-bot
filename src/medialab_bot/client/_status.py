from medialab_bot.client._base import _BaseClient
from medialab_bot.schemas.system import DiskUsageResponse, HealthResponse
from medialab_bot.schemas.transfers import TransferInfoResponse


class _StatusMixin(_BaseClient):
    async def health(self) -> HealthResponse | None:
        data = await self._get("/api/v1/health")
        return self._parse(HealthResponse, data)

    async def get_transfers(self) -> TransferInfoResponse | None:
        data = await self._get("/api/v1/transfers")
        return self._parse(TransferInfoResponse, data)

    async def get_storage(self) -> DiskUsageResponse | None:
        data = await self._get(
            "/api/v1/storage", params={"path": self._tmp_docker_save_path}
        )
        return self._parse(DiskUsageResponse, data)
