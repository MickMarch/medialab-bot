import pytest
from unittest.mock import AsyncMock, MagicMock

from medialab_bot.schemas.system import HealthResponse


@pytest.fixture
def mock_client():
    client = MagicMock()
    client.health = AsyncMock(return_value=HealthResponse(
        status="online",
        uptime_seconds=42.0,
        vpn_interface_bound=True,
    ))
    client.close = AsyncMock()
    return client
