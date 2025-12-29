import os

# Set required env var before importing mcp_obsidian modules
os.environ.setdefault("OBSIDIAN_API_KEY", "test-api-key-for-testing")

import pytest
import responses
from mcp_obsidian.obsidian import Obsidian


@pytest.fixture
def api_key():
    return "test-api-key"


@pytest.fixture
def obsidian_client(api_key):
    return Obsidian(api_key=api_key, protocol="https", host="127.0.0.1", port=27124)


@pytest.fixture
def base_url():
    return "https://127.0.0.1:27124"


@pytest.fixture
def mock_responses():
    with responses.RequestsMock() as rsps:
        yield rsps
