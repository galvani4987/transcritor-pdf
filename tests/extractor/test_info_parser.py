# -*- coding: utf-8 -*-
"""
Unit tests for the src.extractor.info_parser module using FakeListChatModel.
"""

import pytest
import json
from unittest.mock import patch # Still need patch for get_llm_client
# Import the function to test
from src.extractor.info_parser import parse_extracted_info
# Import Langchain components needed for testing
from langchain_core.exceptions import OutputParserException
from langchain_core.messages import AIMessage
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
    Tests successful parsing using FakeListChatModel with a more detailed example.
    """
    # --- Updated Example ---
    sample_raw_text = """Relatório Médico

    Paciente: Maria Oliveira Santos
    Data Atend: 22/04/2025
    Histórico: Paciente refere dor de garganta e febre há 3 dias. Nega outras queixas.
    Exame Físico: Orofaringe hiperemiada, sem placas. Ausculta pulmonar limpa.
    Diagnóstico: Faringite Aguda (CID J02.9)
    Conduta: Prescrito Amoxicilina 500mg 8/8h por 7 dias e repouso.
    Retorno se necessário.

    Dr. Carlos Pereira
    CRM-SP 12345
    (Assinatura Eletrônica)
    """
    expected_parsed_dict = {
        "client_name": "Maria Oliveira Santos",
        "document_date": "2025-04-22", # Assuming LLM can format DD/MM/YYYY
        "signature_found": True, # Based on "Dr. Carlos Pereira" and "(Assinatura Eletrônica)"
        "relevant_illness_mentions": ["dor de garganta", "febre", "Faringite Aguda", "CID J02.9"] # Example extraction
    }
    # --- End Updated Example ---

    mock_llm_response_content_str = json.dumps(expected_parsed_dict)

    # Setup FakeListChatModel
    responses = [ mock_llm_response_content_str ]
    fake_llm = FakeListChatModel(responses=responses)

    # Patch get_llm_client
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
    responses = [ mock_llm_response_content_str ]
    fake_llm = FakeListChatModel(responses=responses)
    mocker.patch('src.extractor.info_parser.get_llm_client', return_value=fake_llm)
    result_dict = parse_extracted_info(sample_raw_text)
    assert result_dict is None

@pytest.mark.skipif(not LANGCHAIN_COMMUNITY_AVAILABLE, reason="langchain-community not installed.")
def test_parse_extracted_info_llm_error(mocker):
    """
    Tests that the function returns None if the FakeListChatModel is configured
    to raise an exception during chain execution.
    """
    sample_raw_text = "Some text."
    simulated_error = Exception("Simulated LLM API Error via FakeListChatModel")
    responses = [ simulated_error ]
    fake_llm = FakeListChatModel(responses=responses)
    mocker.patch('src.extractor.info_parser.get_llm_client', return_value=fake_llm)
    result_dict = parse_extracted_info(sample_raw_text)
    assert result_dict is None

def test_parse_extracted_info_empty_input():
    """
    Tests that the function returns None if the input text is empty or None.
    """
    assert parse_extracted_info("") is None
    assert parse_extracted_info(None) is None # type: ignore
