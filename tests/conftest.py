import pytest
from httpx import AsyncClient, ASGITransport
from unittest.mock import MagicMock, patch

from sidecar.router import app


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.fixture
async def client():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac


@pytest.fixture
def mock_google_service():
    """Mock Google Calendar API service，避免實際呼叫 Google API。"""
    with patch("skills.calendar_gcal.main.get_service") as mock:
        service = MagicMock()
        mock.return_value = service
        yield service
