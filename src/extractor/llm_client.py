# -*- coding: utf-8 -*-
"""
Module for configuring and providing the Large Language Model (LLM) client.

Handles loading API keys from environment variables and initializing the
Langchain client (e.g., ChatOpenAI) configured for the desired service
(like OpenRouter). Includes logging.
"""

import os
import sys
import logging # Import logging
from dotenv import load_dotenv, find_dotenv
# Import the specific Langchain chat model class
try:
    from langchain_openai import ChatOpenAI
except ImportError:
    # Log critical error if dependency is missing
    logging.critical("langchain-openai library not found. Please install it: pip install langchain-openai")
    sys.exit(1)

# Get a logger instance for this module
logger = logging.getLogger(__name__)

# --- Constants ---
OPENAI_API_KEY_VAR = "OPENAI_API_KEY"
OPENAI_BASE_URL_VAR = "OPENAI_BASE_URL"
MODEL_NAME_VAR = "OPENAI_MODEL_NAME" # Or OPENROUTER_MODEL_NAME

DEFAULT_OPENROUTER_BASE_URL = "[https://openrouter.ai/api/v1](https://openrouter.ai/api/v1)"
DEFAULT_MODEL_NAME = "google/gemini-flash"

# --- LLM Client Initialization ---
def load_api_config() -> tuple[str, str, str]:
    """
    Loads API configuration (Key, Base URL, Model Name) from environment variables.

    Returns:
        A tuple containing (api_key, base_url, model_name).
    Raises:
        ValueError: If the API key environment variable is not found.
    """
    env_path = find_dotenv()
    if env_path:
        logger.info(f"Loading environment variables from: {env_path}")
        load_dotenv(dotenv_path=env_path, override=True)
    else:
        logger.warning(".env file not found.")

    # API Key (Mandatory)
    api_key = os.getenv(OPENAI_API_KEY_VAR)
    if not api_key:
        error_msg = f"Required environment variable '{OPENAI_API_KEY_VAR}' not found. Please set it in your .env file (use your OpenRouter key)."
        logger.critical(error_msg) # Use critical as it prevents operation
        raise ValueError(error_msg)

    # Base URL (Optional, with Default)
    base_url = os.getenv(OPENAI_BASE_URL_VAR, DEFAULT_OPENROUTER_BASE_URL)

    # Model Name (Optional, with Default)
    model_name = os.getenv(MODEL_NAME_VAR) or os.getenv("OPENROUTER_MODEL_NAME", DEFAULT_MODEL_NAME)

    # Log loaded config (excluding API key)
    logger.info(f"API Config Loaded: Base URL='{base_url}', Model Name='{model_name}'")
    return api_key, base_url, model_name

_llm_client = None

def get_llm_client():
    """
    Initializes and returns a Langchain Chat Model client configured for OpenRouter.

    Returns:
        An initialized Langchain ChatOpenAI client instance.
    Raises:
        ValueError: If the API key is not found during the first call.
        RuntimeError: If any other initialization error occurs.
    """
    global _llm_client
    if _llm_client is None:
        logger.info("Initializing LLM client for the first time...")
        try:
            api_key, base_url, model_name = load_api_config()

            logger.info("Configuring Langchain ChatOpenAI client:")
            logger.info(f"  Model: {model_name}")
            logger.info(f"  Base URL: {base_url}")
            # Do NOT log the API key

            _llm_client = ChatOpenAI(
                model=model_name,
                openai_api_key=api_key,
                openai_api_base=base_url,
                # temperature=0.5, # Optional parameters
                # max_tokens=2048,
                # request_timeout=60,
                # max_retries=2,
            )
            logger.info("LLM client initialized successfully.")

        except ValueError as e:
            # API key not found error already logged in load_api_config
            raise # Re-raise the ValueError
        except Exception as e:
            logger.critical(f"Failed to initialize LLM client: {e}", exc_info=True)
            raise RuntimeError(f"Failed to initialize LLM client: {e}") from e

    return _llm_client

# Example usage block (for testing when script is run directly)
if __name__ == "__main__":
    # Configure logging for test run
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(name)s - %(message)s')
    logger.info("--- Running llm_client.py directly for testing ---")
    logger.info(f"Ensure .env file exists with '{OPENAI_API_KEY_VAR}' set.")
    logger.info(f"Optional vars: '{OPENAI_BASE_URL_VAR}', '{MODEL_NAME_VAR}'")

    try:
        client = get_llm_client()
        logger.info("Test successful: LLM Client object created.")

        logger.info("Calling get_llm_client() again...")
        client_again = get_llm_client()
        if client is client_again:
             logger.info("Successfully retrieved the same client instance.")
        else:
             logger.warning("A new client instance was created on the second call.")

        # Optional test call (commented out by default)
        # logger.info("Attempting a simple test call to the LLM...")
        # try:
        #     from langchain_core.prompts import ChatPromptTemplate
        #     prompt = ChatPromptTemplate.from_messages([("system", "You are helpful."), ("user", "{input}")])
        #     chain = prompt | client
        #     response = chain.invoke({"input": "What is OpenRouter in one sentence?"})
        #     if hasattr(response, 'content'): logger.info(f"Test call response: {response.content}")
        #     else: logger.info(f"Test call response (raw): {response}")
        # except ImportError: logger.warning("Skipping test call: langchain-core components not found.")
        # except Exception as call_error: logger.error(f"Error during test call: {call_error}", exc_info=True)

    except (ValueError, RuntimeError) as e:
         logger.error(f"Test failed during client initialization: {e}")
    except Exception as e:
         logger.error(f"An unexpected error occurred during testing: {e}", exc_info=True)

    logger.info("--- LLM Client Test Complete ---")