import logging
from typing import Self

import httpx
from pydantic import BaseModel, ValidationError

logger = logging.getLogger(__name__)


class _BaseClient:
    def __init__(self, base_url: str, api_key: str, save_path: str, torrent_search_timeout: float = 30.0) -> None:
        self._http = httpx.AsyncClient(
            base_url=base_url,
            headers={"X-API-Key": api_key},
        )
        self._save_path = save_path
        self._torrent_search_timeout = torrent_search_timeout

    async def _get(self, path: str, params: dict | None = None, timeout: float | None = None) -> dict | None:
        try:
            response = await self._http.get(path, params=params or {}, timeout=timeout)
            if response.status_code != 200:
                logger.warning("GET %s returned %d", path, response.status_code)
                return None
            return response.json()
        except httpx.TimeoutException:
            logger.warning("GET %s timed out", path)
            return None
        except (httpx.ConnectError, httpx.HTTPError):
            logger.warning("GET %s failed with network error", path)
            return None
        except ValueError:
            logger.error("GET %s returned non-JSON response", path)
            return None

    async def _post(self, path: str, json: dict | None = None, expected_status: int = 200) -> dict | None:
        try:
            response = await self._http.post(path, json=json or {})
            if response.status_code != expected_status:
                logger.warning("POST %s returned %d", path, response.status_code)
                return None
            return response.json()
        except httpx.TimeoutException:
            logger.warning("POST %s timed out", path)
            return None
        except (httpx.ConnectError, httpx.HTTPError):
            logger.warning("POST %s failed with network error", path)
            return None
        except ValueError:
            logger.error("POST %s returned non-JSON response", path)
            return None

    @staticmethod
    def _parse(model: type[BaseModel], data: dict | None) -> BaseModel | None:
        if data is None:
            return None
        try:
            return model.model_validate(data)
        except (ValidationError, TypeError) as exc:
            logger.error("Failed to parse %s: %s", model.__name__, exc)
            return None

    async def close(self) -> None:
        await self._http.aclose()

    async def __aenter__(self) -> Self:
        return self

    async def __aexit__(self, *_) -> None:
        await self.close()
