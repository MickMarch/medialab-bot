from unittest.mock import AsyncMock, MagicMock

import pytest

from medialab_bot.schemas.system import DownstreamHealth, HealthResponse


@pytest.fixture
def mock_client():
    client = MagicMock()
    client.health = AsyncMock(
        return_value=HealthResponse(
            status="online",
            uptime_seconds=42.0,
            downstream=DownstreamHealth(torrent_downloader=True, medialab_jellyfin=True),
        )
    )
    client.close = AsyncMock()
    return client


@pytest.fixture
def mock_config():
    config = MagicMock()
    config.select_max_results = 25
    config.torrent_results_per_resolution = 5
    return config
