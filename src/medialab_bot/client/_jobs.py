from medialab_bot.client._base import _BaseClient
from medialab_bot.schemas.jobs import JobsResponse, JobView


class _JobsMixin(_BaseClient):
    async def list_jobs(self, status: str | None = None) -> JobsResponse | None:
        params = {"status": status} if status else None
        data = await self._get("/api/v1/jobs", params=params)
        return self._parse(JobsResponse, data)

    async def retry_job(self, torrent_hash: str) -> JobView | None:
        # The gateway re-enters the worker from the last good state and returns
        # the updated job (not wrapped in a status envelope).
        data = await self._post(f"/api/v1/jobs/{torrent_hash}/retry")
        return self._parse(JobView, data)
