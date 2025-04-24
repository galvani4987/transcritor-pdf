# -*- coding: utf-8 -*-
"""
Unit tests for the src.vectorizer.vector_store_handler module using asyncpg mocks.
"""

import pytest
import json
import asyncio
from unittest.mock import MagicMock, AsyncMock, patch
from src.vectorizer.vector_store_handler import add_chunks_to_vector_store, load_db_config
try:
    import asyncpg # Import asyncpg to reference its exceptions
    ASYNC_PG_AVAILABLE = True
except ImportError:
    ASYNC_PG_AVAILABLE = False

pytestmark = pytest.mark.asyncio

@pytest.fixture
def mock_db_config(mocker):
    dummy_config = {"host": "mockhost", "port": 5432, "database": "mockdb", "user": "mockuser", "password": "mockpassword"}
    mocker.patch('src.vectorizer.vector_store_handler.load_db_config', return_value=dummy_config)
    return dummy_config

@pytest.fixture
def mock_asyncpg_connect(mocker):
    if not ASYNC_PG_AVAILABLE: pytest.skip("asyncpg not installed")
    mock_conn = AsyncMock(spec=asyncpg.Connection)
    # Mock the transaction context manager
    mock_tx = AsyncMock()
    # __aexit__ needs to handle exception propagation correctly for the test
    # If side_effect is set on execute, __aexit__ will receive exception info
    async def mock_aexit(exc_type, exc_val, exc_tb):
        # Simulate default behavior: re-raise if exception occurred
        # print(f"DEBUG: __aexit__ called with exc_type={exc_type}") # Debug print
        if exc_type:
            return False # Indicates exception should be re-raised
        return True # Indicates exception was handled (suppressed)

    mock_conn.transaction.return_value = mocker.AsyncMock(
        __aenter__=AsyncMock(return_value=mock_tx),
        __aexit__=AsyncMock(side_effect=mock_aexit) # Use side_effect for async func
    )
    mock_conn.execute = AsyncMock()
    mock_conn.close = AsyncMock()
    mock_conn.is_closed.return_value = False
    mock_connect = mocker.patch('asyncpg.connect', new_callable=AsyncMock, return_value=mock_conn)
    return mock_connect, mock_conn

@pytest.mark.skipif(not ASYNC_PG_AVAILABLE, reason="asyncpg not installed.")
async def test_add_chunks_success(mock_db_config, mock_asyncpg_connect):
    mock_connect, mock_conn = mock_asyncpg_connect
    embedding_dim = 1536
    sample_chunks = [
        {"chunk_id": "ok_chunk_1", "text_content": "Text 1.", "metadata": {"p": 1}, "embedding": [0.1] * embedding_dim},
        {"chunk_id": "ok_chunk_2", "text_content": "Text 2.", "metadata": {"p": 2}, "embedding": [0.2] * embedding_dim},
    ]
    await add_chunks_to_vector_store(sample_chunks)
    mock_connect.assert_awaited_once_with(**mock_db_config)
    mock_conn.transaction.assert_called_once()
    assert mock_conn.execute.await_count == 2
    mock_conn.close.assert_awaited_once()

@pytest.mark.skipif(not ASYNC_PG_AVAILABLE, reason="asyncpg not installed.")
async def test_add_chunks_skips_invalid(mock_db_config, mock_asyncpg_connect):
    mock_connect, mock_conn = mock_asyncpg_connect
    embedding_dim = 1536
    sample_chunks = [
        {"chunk_id": "valid_1", "text_content": "Valid text.", "metadata": {}, "embedding": [0.1] * embedding_dim},
        {"chunk_id": "invalid_1", "text_content": "Missing embedding.", "metadata": {}},
        {"chunk_id": "valid_2", "text_content": "Another valid.", "metadata": {}, "embedding": [0.2] * embedding_dim},
        {"chunk_id": "invalid_2", "text_content": None, "metadata": {}, "embedding": [0.3] * embedding_dim},
    ]
    await add_chunks_to_vector_store(sample_chunks)
    mock_connect.assert_awaited_once()
    mock_conn.transaction.assert_called_once()
    assert mock_conn.execute.await_count == 2
    mock_conn.close.assert_awaited_once()

@pytest.mark.skipif(not ASYNC_PG_AVAILABLE, reason="asyncpg not installed.")
async def test_add_chunks_connection_error(mock_db_config, mocker):
    mock_connect = mocker.patch('asyncpg.connect', new_callable=AsyncMock)
    mock_connect.side_effect = OSError("Simulated connection refused")
    sample_chunks = [{"chunk_id": "c1", "text_content": "t", "metadata": {}, "embedding": [0.1]}]
    # Expect ConnectionError because the outer except block catches OSError
    with pytest.raises(ConnectionError):
        await add_chunks_to_vector_store(sample_chunks)
    mock_connect.assert_awaited_once_with(**mock_db_config)

@pytest.mark.skipif(not ASYNC_PG_AVAILABLE, reason="asyncpg not installed.")
async def test_add_chunks_execute_error(mock_db_config, mock_asyncpg_connect):
    """
    Tests that ConnectionError is raised if conn.execute fails internally,
    due to the outer exception handling wrapping the original asyncpg error.
    """
    mock_connect, mock_conn = mock_asyncpg_connect
    embedding_dim = 1536
    sample_chunks = [{"chunk_id": "c1", "text_content": "t", "metadata": {}, "embedding": [0.1] * embedding_dim}]

    # Simulate asyncpg error during execute
    db_error = asyncpg.PostgresError("Simulated unique constraint violation")
    mock_conn.execute.side_effect = db_error

    # --- Expect ConnectionError, as the original error is caught and wrapped ---
    with pytest.raises(ConnectionError):
        await add_chunks_to_vector_store(sample_chunks)
    # --- End Correction ---

    # Assertions
    mock_connect.assert_awaited_once()
    mock_conn.transaction.assert_called_once()
    mock_conn.execute.assert_awaited_once() # Should be called once before failing
    mock_conn.close.assert_awaited_once() # Finally block should still close

async def test_add_chunks_empty_list():
    """Tests that the function handles an empty input list gracefully."""
    await add_chunks_to_vector_store([])
