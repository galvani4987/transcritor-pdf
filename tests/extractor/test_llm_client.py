# -*- coding: utf-8 -*-
"""
Unit tests for the src.extractor.llm_client module using mocks.
"""

import pytest
import os
# Import the module/functions to test
import src.extractor.llm_client as llm_client_module
from src.extractor.llm_client import get_llm_client, load_api_config
# Import the class we need to mock
from langchain_openai import ChatOpenAI

# --- Fixtures ---

@pytest.fixture(autouse=True)
def clear_llm_client_cache():
    """Fixture to automatically reset the cached client before each test."""
    llm_client_module._llm_client = None
    yield
    llm_client_module._llm_client = None

# --- Test Cases ---

def test_get_llm_client_success(mocker):
    """
    Tests successful initialization and singleton behavior of get_llm_client.
    """
    mock_api_key = "fake-api-key"
    mock_base_url = "[http://mock.url/v1](http://mock.url/v1)"
    mock_model_name = "mock-model"

    def mock_getenv(key, default=None):
        if key == llm_client_module.OPENAI_API_KEY_VAR: return mock_api_key
        if key == llm_client_module.OPENAI_BASE_URL_VAR: return mock_base_url
        if key == llm_client_module.MODEL_NAME_VAR: return mock_model_name
        # Handle ALT_MODEL_NAME_VAR correctly based on whether MODEL_NAME_VAR is mocked
        if key == llm_client_module.ALT_MODEL_NAME_VAR:
             # If MODEL_NAME_VAR was mocked, ALT should return None/default
             # This assumes MODEL_NAME_VAR takes precedence if both are set, which matches the code
             if os.getenv(llm_client_module.MODEL_NAME_VAR) == mock_model_name:
                 return default
             else: # Otherwise, return its mocked value if needed, or default
                 return default # Adjust if testing ALT_MODEL_NAME_VAR specifically
        return default # Return default for any other key
    mocker.patch('os.getenv', side_effect=mock_getenv)

    mock_chat_openai_class = mocker.patch('src.extractor.llm_client.ChatOpenAI')
    mock_chat_openai_instance = mocker.MagicMock(spec=ChatOpenAI)
    mock_chat_openai_class.return_value = mock_chat_openai_instance

    # First Call
    client1 = get_llm_client()
    os.getenv.assert_any_call(llm_client_module.OPENAI_API_KEY_VAR)
    mock_chat_openai_class.assert_called_once_with(
        model=mock_model_name,
        openai_api_key=mock_api_key,
        openai_api_base=mock_base_url
    )
    assert client1 is mock_chat_openai_instance

    # Second Call
    client2 = get_llm_client()
    mock_chat_openai_class.assert_called_once() # Still called only once
    assert client2 is client1

def test_get_llm_client_missing_api_key(mocker):
    """
    Tests that get_llm_client raises ValueError if OPENAI_API_KEY is not set.
    """
    def mock_getenv_no_key(key, default=None):
        if key == llm_client_module.OPENAI_API_KEY_VAR: return None
        # Provide other defaults to allow load_api_config to proceed until key check
        if key == llm_client_module.OPENAI_BASE_URL_VAR: return llm_client_module.DEFAULT_OPENROUTER_BASE_URL
        if key == llm_client_module.MODEL_NAME_VAR: return llm_client_module.DEFAULT_MODEL_NAME
        if key == llm_client_module.ALT_MODEL_NAME_VAR: return None
        return default
    mocker.patch('os.getenv', side_effect=mock_getenv_no_key)

    with pytest.raises(ValueError) as excinfo:
        get_llm_client()
    assert llm_client_module.OPENAI_API_KEY_VAR in str(excinfo.value)

def test_load_api_config_uses_defaults(mocker):
    """
    Tests that load_api_config uses default values if env vars are not set
    (except for the mandatory API key).
    """
    mock_api_key = "fake-key-for-defaults-test"
    # --- CORRECTION HERE ---
    # Mock os.getenv to return the API key OR the default value passed to it
    mocker.patch('os.getenv', lambda key, default=None: mock_api_key if key == llm_client_module.OPENAI_API_KEY_VAR else default)
    # --- END CORRECTION ---

    api_key, base_url, model_name = load_api_config()

    assert api_key == mock_api_key
    assert base_url == llm_client_module.DEFAULT_OPENROUTER_BASE_URL # Should now get default
    assert model_name == llm_client_module.DEFAULT_MODEL_NAME # Should now get default

def test_load_api_config_uses_env_vars(mocker):
    """
    Tests that load_api_config correctly reads values from environment variables.
    """
    mock_api_key = "env-api-key"
    mock_base_url = "[http://env.url/v1](http://env.url/v1)"
    mock_model_name = "env-model"

    # Mock os.getenv using a dictionary lookup for clarity
    env_vars = {
        llm_client_module.OPENAI_API_KEY_VAR: mock_api_key,
        llm_client_module.OPENAI_BASE_URL_VAR: mock_base_url,
        llm_client_module.MODEL_NAME_VAR: mock_model_name
    }
    mocker.patch('os.getenv', lambda key, default=None: env_vars.get(key, default))

    api_key, base_url, model_name = load_api_config()

    assert api_key == mock_api_key
    assert base_url == mock_base_url
    assert model_name == mock_model_name