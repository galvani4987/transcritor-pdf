# -*- coding: utf-8 -*-
"""
Unit tests for the src.extractor.text_extractor module using mocks.
"""

import pytest
import base64
from unittest.mock import MagicMock, patch # Import patch for mocking module functions
from PIL import Image
# Import the functions to test
from src.extractor.text_extractor import extract_text_from_image, encode_image_to_base64
# Import the Langchain message class to check prompt structure
from langchain_core.messages import HumanMessage

# --- Helper Functions / Fixtures ---

def create_dummy_image(mode='RGB', size=(10, 10), color='red') -> Image.Image:
    """Creates a simple dummy PIL Image."""
    return Image.new(mode, size, color)

@pytest.fixture
def mock_llm_client(mocker) -> MagicMock:
    """Fixture to mock the LLM client obtained via get_llm_client."""
    # Create a mock object to simulate the LLM client instance
    mock_client = mocker.MagicMock()

    # Mock the get_llm_client function *within the text_extractor module*
    # to return our mock_client instance instead of initializing the real one.
    mocker.patch('src.extractor.text_extractor.get_llm_client', return_value=mock_client)
    return mock_client

# --- Test Cases ---

def test_encode_image_to_base64():
    """Tests the helper function for base64 encoding."""
    img = create_dummy_image()
    b64_uri = encode_image_to_base64(img, format="PNG") # Test with PNG for variety
    assert isinstance(b64_uri, str)
    assert b64_uri.startswith("data:image/png;base64,")
    # Decode to check if it's valid base64 (doesn't check content)
    try:
        base64.b64decode(b64_uri.split(",", 1)[1])
    except Exception as e:
        pytest.fail(f"Base64 decoding failed: {e}")

def test_extract_text_success(mock_llm_client: MagicMock):
    """
    Tests successful text extraction using a mocked LLM client.
    """
    dummy_image = create_dummy_image()
    expected_text = "This is the mocked extracted text."

    # Configure the mock LLM client's invoke method to return a mock response
    # The response structure from invoke might be the message itself, not a list
    # Let's assume invoke returns an AIMessage-like object with a 'content' attribute
    mock_response = MagicMock()
    mock_response.content = expected_text
    mock_llm_client.invoke.return_value = mock_response # Adjusted: invoke returns the response directly

    # --- Call the function under test ---
    result_text = extract_text_from_image(dummy_image)

    # --- Assertions ---
    mock_llm_client.invoke.assert_called_once()
    args, kwargs = mock_llm_client.invoke.call_args
    assert len(args) == 1
    message_list = args[0]
    assert isinstance(message_list, list) and len(message_list) == 1
    human_message = message_list[0]
    assert isinstance(human_message, HumanMessage)
    assert isinstance(human_message.content, list) and len(human_message.content) == 2
    assert human_message.content[0]['type'] == 'text'
    assert human_message.content[1]['type'] == 'image_url'
    assert human_message.content[1]['image_url']['url'].startswith("data:image/webp;base64,")
    assert result_text == expected_text

def test_extract_text_llm_error(mock_llm_client: MagicMock):
    """
    Tests that the function returns None if the LLM call raises an exception.
    """
    dummy_image = create_dummy_image()
    mock_llm_client.invoke.side_effect = Exception("Simulated API Error")
    result_text = extract_text_from_image(dummy_image)
    assert result_text is None

def test_extract_text_invalid_response(mock_llm_client: MagicMock):
    """
    Tests that the function returns None if the LLM response is not as expected.
    """
    dummy_image = create_dummy_image()
    # Simulate response missing 'content'
    mock_response = MagicMock(spec=['some_other_attribute']) # Does not have 'content'
    mock_llm_client.invoke.return_value = mock_response
    result_text = extract_text_from_image(dummy_image)
    assert result_text is None

def test_extract_text_invalid_input_type():
    """
    Tests that a TypeError is raised if the input is not a PIL Image.
    """
    with pytest.raises(TypeError):
        extract_text_from_image("this is not an image")