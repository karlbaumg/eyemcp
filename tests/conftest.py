"""
Pytest configuration file for EyeMCP tests.

This file contains fixtures and configuration for the pytest test suite.
"""

import pytest
import asyncio


# Configure pytest to handle asyncio tests
@pytest.fixture
def event_loop():
    """Create an instance of the default event loop for each test case."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()
