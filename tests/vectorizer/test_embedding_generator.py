# -*- coding: utf-8 -*-
"""
Unit tests for the src.vectorizer.embedding_generator module using mocks.
"""

import pytest
import sys
# Import the module/functions to test
import src.vectorizer.embedding_generator as embedding_generator_module
from src.vectorizer.embedding_generator import get_embedding_client, generate_embeddings_for_chunks
# Import the class to mock
try:
    # Try importing the real class to check if the library is installed
    from langchain_openai import OpenAIEmbeddings
    LANGCHAIN_OPENAI_AVAILABLE = True
except ImportError:
    LANGCHAIN_OPENAI_AVAILABLE = False
    # Define a dummy class if the real one isn't available,
    # so the module can be imported by pytest, but tests requiring it will skip.
    class OpenAIEmbeddings: pass


# --- Fixtures ---

@pytest.fixture(autouse=True)
def clear_embedding_client_cache():
    """Fixture to automatically reset the cached client before each test."""
    embedding_generator_module._embedding_client = None
    yield
    embedding_generator_module._embedding_client = None

@pytest.fixture
def mock_openai_embeddings(mocker):
    """Fixture to mock the OpenAIEmbeddings class and its methods."""
    if not LANGCHAIN_OPENAI_AVAILABLE:
        pytest.skip("langchain-openai not installed, skipping tests requiring it.")

    # Mock the class within the embedding_generator module's namespace
    mock_class = mocker.patch('src.vectorizer.embedding_generator.OpenAIEmbeddings')

    # Create a mock instance that the class will return upon initialization
    mock_instance = mocker.MagicMock(spec=OpenAIEmbeddings)

    # Define the mock behavior for the embed_documents method
    # Example: Return dummy embeddings based on input length
    dummy_dim = embedding_generator_module.EMBEDDING_DIMENSIONS or 1536 # Use configured or default dim
    def mock_embed_documents(texts: list[str]):
        print(f"Mock embed_documents called with {len(texts)} texts.") # Debug print
        # Return a list of dummy vectors, one for each input text
        return [[float(i+1)/10] * dummy_dim for i, _ in enumerate(texts)]

    mock_instance.embed_documents.side_effect = mock_embed_documents

    # Configure the mocked class to return the mocked instance
    mock_class.return_value = mock_instance
    # Return the mock instance so tests can make assertions on it if needed
    return mock_instance


# --- Test Cases ---

def test_get_embedding_client_success(mocker, mock_openai_embeddings):
    """
    Tests successful initialization and singleton behavior of get_embedding_client.
    Relies on the mock_openai_embeddings fixture.
    """
    # Mock os.getenv for API key check if needed (though OpenAIEmbeddings might not need explicit key if env var set)
    # For simplicity, assume API key env var exists for initialization check
    mocker.patch('os.getenv', lambda key, default=None: "fake-key" if key == "OPENAI_API_KEY" else default)

    # --- First Call: Initialization ---
    client1 = get_embedding_client()
    # Assert that the mock instance returned by the fixture was used
    assert client1 is mock_openai_embeddings
    # Check if OpenAIEmbeddings was called with expected args (using the mock class)
    embedding_generator_module.OpenAIEmbeddings.assert_called_once_with(
        model=embedding_generator_module.EMBEDDING_MODEL_NAME,
        dimensions=embedding_generator_module.EMBEDDING_DIMENSIONS
    )

    # --- Second Call: Singleton Check ---
    client2 = get_embedding_client()
    # Check that the class was NOT initialized again
    embedding_generator_module.OpenAIEmbeddings.assert_called_once()
    # Check that the same instance is returned
    assert client2 is client1

@pytest.mark.skipif(not LANGCHAIN_OPENAI_AVAILABLE, reason="langchain-openai not installed.")
def test_generate_embeddings_success(mocker, mock_openai_embeddings):
    """
    Tests successful embedding generation for a list of chunks.
    """
    # Sample input chunks
    sample_chunks = [
        {"chunk_id": "c1", "text_content": "Text 1", "metadata": {}},
        {"chunk_id": "c2", "text_content": "Text 2", "metadata": {}},
    ]
    expected_texts = ["Text 1", "Text 2"]
    dummy_dim = embedding_generator_module.EMBEDDING_DIMENSIONS or 1536

    # --- Call the function ---
    # The get_embedding_client call inside will use the mocked instance
    result_chunks = generate_embeddings_for_chunks(sample_chunks)

    # --- Assertions ---
    # 1. Check if embed_documents was called correctly on the mock instance
    mock_openai_embeddings.embed_documents.assert_called_once_with(expected_texts)

    # 2. Check if the 'embedding' key was added and has the correct format/dimension
    assert len(result_chunks) == 2
    assert 'embedding' in result_chunks[0]
    assert isinstance(result_chunks[0]['embedding'], list)
    assert len(result_chunks[0]['embedding']) == dummy_dim
    assert result_chunks[0]['embedding'][0] == 0.1 # Based on our mock_embed_documents logic

    assert 'embedding' in result_chunks[1]
    assert isinstance(result_chunks[1]['embedding'], list)
    assert len(result_chunks[1]['embedding']) == dummy_dim
    assert result_chunks[1]['embedding'][0] == 0.2 # Based on our mock_embed_documents logic

@pytest.mark.skipif(not LANGCHAIN_OPENAI_AVAILABLE, reason="langchain-openai not installed.")
def test_generate_embeddings_skips_empty_text(mocker, mock_openai_embeddings):
    """
    Tests that chunks with empty or None text_content are skipped and get embedding=None.
    """
    sample_chunks = [
        {"chunk_id": "c1", "text_content": "Valid text", "metadata": {}},
        {"chunk_id": "c2", "text_content": "", "metadata": {}}, # Empty string
        {"chunk_id": "c3", "text_content": None, "metadata": {}}, # None value
        {"chunk_id": "c4", "metadata": {}}, # Missing key
    ]
    expected_texts_to_embed = ["Valid text"] # Only the first chunk's text
    dummy_dim = embedding_generator_module.EMBEDDING_DIMENSIONS or 1536

    # Call the function
    result_chunks = generate_embeddings_for_chunks(sample_chunks)

    # Assertions
    # embed_documents should only be called with the valid text
    mock_openai_embeddings.embed_documents.assert_called_once_with(expected_texts_to_embed)

    # Check the results for each chunk
    assert isinstance(result_chunks[0].get('embedding'), list) # Chunk 1 should have embedding
    assert len(result_chunks[0]['embedding']) == dummy_dim

    assert result_chunks[1].get('embedding') is None # Chunk 2 should be None
    assert result_chunks[2].get('embedding') is None # Chunk 3 should be None
    assert result_chunks[3].get('embedding') is None # Chunk 4 should be None

def test_generate_embeddings_empty_input_list():
    """Tests that an empty list is returned if the input list is empty."""
    result = generate_embeddings_for_chunks([])
    assert result == []

# Add more tests later:
# - Test handling of API errors raised by the mocked embed_documents
# - Test behavior if embedding dimension mismatch occurs (if checking is added)