# -*- coding: utf-8 -*-
"""
Unit tests for the src.extractor.info_parser module using FakeListChatModel.
Trying simplified response list for FakeListChatModel.
"""

import pytest
import json
from unittest.mock import patch
# Import the function to test
from src.extractor.info_parser import parse_extracted_info
# Import Langchain components needed for testing
from langchain_core.exceptions import OutputParserException
from langchain_core.messages import AIMessage # Keep for type hints if needed elsewhere
# Import the FakeListChatModel
try:
    from langchain_community.chat_models.fake import FakeListChatModel
    LANGCHAIN_COMMUNITY_AVAILABLE = True
except ImportError:
    LANGCHAIN_COMMUNITY_AVAILABLE = False
    class FakeListChatModel: pass # Dummy for skipping

# --- Test Cases ---

@pytest.mark.skipif(not LANGCHAIN_COMMUNITY_AVAILABLE, reason="langchain-community not installed.")
def test_parse_extracted_info_success(mocker):
    """
    Tests successful parsing using FakeListChatModel simulating LLM response string.
    """
    sample_raw_text = "Patient John Doe, DOB 1980-05-10. Diagnosis: Flu. Signed: Dr. Smith."
    expected_parsed_dict = {
        "client_name": "John Doe",
        "document_date": None,
        "signature_found": True,
        "relevant_illness_mentions": ["Flu"]
    }
    mock_llm_response_content_str = json.dumps(expected_parsed_dict)

    # --- Setup FakeListChatModel with STRING response ---
    # Pass the string directly, hoping FakeListChatModel wraps it correctly.
    responses = [ mock_llm_response_content_str ]
    fake_llm = FakeListChatModel(responses=responses)
    # --- End Setup ---

    # Patch get_llm_client to return the fake LLM
    mocker.patch('src.extractor.info_parser.get_llm_client', return_value=fake_llm)

    # Call the function under test
    result_dict = parse_extracted_info(sample_raw_text)

    # Assertions
    assert result_dict == expected_parsed_dict

@pytest.mark.skipif(not LANGCHAIN_COMMUNITY_AVAILABLE, reason="langchain-community not installed.")
def test_parse_extracted_info_llm_returns_malformed_json(mocker):
    """
    Tests parser failure when FakeListChatModel returns malformed JSON string.
    """
    sample_raw_text = "Some text leading to bad JSON."
    mock_llm_response_content_str = "This is not JSON { maybe name: John }"

    # --- Setup FakeListChatModel with STRING response ---
    responses = [ mock_llm_response_content_str ]
    fake_llm = FakeListChatModel(responses=responses)
    # --- End Setup ---

    # Patch get_llm_client
    mocker.patch('src.extractor.info_parser.get_llm_client', return_value=fake_llm)

    # Call the function under test
    # The real JsonOutputParser should fail here
    result_dict = parse_extracted_info(sample_raw_text)

    # Assertions
    assert result_dict is None

@pytest.mark.skipif(not LANGCHAIN_COMMUNITY_AVAILABLE, reason="langchain-community not installed.")
def test_parse_extracted_info_llm_error(mocker):
    """
    Tests that the function returns None if the FakeListChatModel is configured
    to raise an exception during chain execution.
    """
    sample_raw_text = "Some text."

    # --- Setup FakeListChatModel to raise an error ---
    simulated_error = Exception("Simulated LLM API Error via FakeListChatModel")
    # Passing an exception still seems the correct way for error simulation
    responses = [ simulated_error ]
    fake_llm = FakeListChatModel(responses=responses)
    # --- End Setup ---

    # Patch get_llm_client
    mocker.patch('src.extractor.info_parser.get_llm_client', return_value=fake_llm)

    # Call the function under test
    result_dict = parse_extracted_info(sample_raw_text)

    # Assertions
    assert result_dict is None

def test_parse_extracted_info_empty_input():
    """
    Tests that the function returns None if the input text is empty or None.
    """
    assert parse_extracted_info("") is None
    assert parse_extracted_info(None) is None # type: ignore
