# -*- coding: utf-8 -*-
"""
Module for configuring and providing the Large Language Model (LLM) client.

Handles loading API keys from environment variables and initializing the
Langchain client (e.g., ChatOpenAI) configured for the desired service
(like OpenRouter).
"""

import os
import sys
from dotenv import load_dotenv, find_dotenv # Added find_dotenv for robustness
# Import the specific Langchain chat model class we'll use
# Using ChatOpenAI as OpenRouter often provides an OpenAI-compatible endpoint
from langchain_openai import ChatOpenAI
# from langchain_core.language_models.chat_models import BaseChatModel # For type hinting

# --- Constants ---
# Environment variable names - Using standard OpenAI names where possible for compatibility
# User should set OPENAI_API_KEY in .env to their OpenRouter key
OPENAI_API_KEY_VAR = "OPENAI_API_KEY" # Use this standard name in .env for the OpenRouter key
# User should set OPENAI_BASE_URL in .env to the OpenRouter endpoint
OPENAI_BASE_URL_VAR = "OPENAI_BASE_URL"
# User can set OPENROUTER_MODEL_NAME or OPENAI_MODEL_NAME in .env
MODEL_NAME_VAR = "OPENAI_MODEL_NAME" # Or OPENROUTER_MODEL_NAME

# Default values (can be overridden by .env file)
DEFAULT_OPENROUTER_BASE_URL = "[https://openrouter.ai/api/v1](https://openrouter.ai/api/v1)" # Common base URL
DEFAULT_MODEL_NAME = "google/gemini-flash" # Example default model

# --- LLM Client Initialization ---
def load_api_config() -> tuple[str, str, str]:
    """
    Loads API configuration (Key, Base URL, Model Name) from environment variables.

    Searches for a .env file and loads it.

    Returns:
        A tuple containing (api_key, base_url, model_name).

    Raises:
        ValueError: If the API key environment variable is not found.
    """
    # Load environment variables from .env file if it exists
    # find_dotenv() searches parent directories, useful if script runs from subdir
    env_path = find_dotenv()
    if env_path:
        print(f"Loading environment variables from: {env_path}")
        load_dotenv(dotenv_path=env_path, override=True)
    else:
        print("Warning: .env file not found.", file=sys.stderr)

    # --- API Key (Mandatory) ---
    api_key = os.getenv(OPENAI_API_KEY_VAR)
    if not api_key:
        error_msg = f"Error: Required environment variable '{OPENAI_API_KEY_VAR}' not found. Please set it in your .env file (use your OpenRouter key)."
        print(error_msg, file=sys.stderr)
        raise ValueError(error_msg)

    # --- Base URL (Optional, with Default) ---
    base_url = os.getenv(OPENAI_BASE_URL_VAR, DEFAULT_OPENROUTER_BASE_URL)

    # --- Model Name (Optional, with Default) ---
    # Allow flexibility in naming the env var
    model_name = os.getenv(MODEL_NAME_VAR) or os.getenv("OPENROUTER_MODEL_NAME", DEFAULT_MODEL_NAME)

    return api_key, base_url, model_name


# Store the client globally within the module after first initialization?
# This avoids re-initializing the client every time it's needed, but makes
# it harder to change configuration dynamically if needed later.
# For a CLI tool usually run once per execution, initializing once is fine.
_llm_client = None

def get_llm_client(): # Use BaseChatModel for type hint flexibility -> Can't use it now
    """
    Initializes and returns a Langchain Chat Model client configured for OpenRouter.

    If called multiple times, returns the previously initialized client instance.
    Reads configuration on first call.

    Returns:
        An initialized Langchain ChatOpenAI client instance.

    Raises:
        ValueError: If the API key is not found during the first call.
        RuntimeError: If any other initialization error occurs.
    """
    global _llm_client
    if _llm_client is None:
        print("Initializing LLM client for the first time...")
        try:
            api_key, base_url, model_name = load_api_config()

            print(f"  Configuring Langchain client:")
            print(f"    Model: {model_name}")
            print(f"    Base URL: {base_url}")
            # Do NOT print the API key for security

            # Initialize the ChatOpenAI client from Langchain
            # Configure it to point to the OpenRouter endpoint
            _llm_client = ChatOpenAI(
                model=model_name,
                openai_api_key=api_key,
                openai_api_base=base_url,
                # --- Optional Parameters ---
                # temperature=0.5, # Example: Balance creativity and predictability
                # max_tokens=2048, # Example: Set response length limit
                # request_timeout=60, # Example: Set timeout for API calls (seconds)
                # max_retries=2, # Example: Retry failed requests automatically
            )
            print("LLM client initialized successfully.")

        except ValueError as e:
            # API key not found error from load_api_config
            raise # Re-raise the ValueError
        except Exception as e:
            # Catch other potential initialization errors
            error_msg = f"Failed to initialize LLM client: {e}"
            print(error_msg, file=sys.stderr)
            raise RuntimeError(error_msg) from e # Wrap other errors

    return _llm_client

# Example usage block (for testing when script is run directly)
if __name__ == "__main__":
    print("\n--- Running llm_client.py directly for testing ---")
    print(f"Make sure you have a .env file in the project root or parent directory with:")
    print(f"  {OPENAI_API_KEY_VAR}=your_actual_openrouter_key")
    print(f"Optionally add:")
    print(f"  {OPENAI_BASE_URL_VAR}={DEFAULT_OPENROUTER_BASE_URL}")
    print(f"  {MODEL_NAME_VAR}={DEFAULT_MODEL_NAME} (or another model like 'mistralai/mistral-7b-instruct')")

    try:
        client = get_llm_client() # First call initializes
        print("\nTest successful: LLM Client object created:")
        # print(client) # Printing the client object can be verbose

        # Test getting the client again (should return the same instance)
        print("\nCalling get_llm_client() again...")
        client_again = get_llm_client()
        if client is client_again:
             print("Successfully retrieved the same client instance.")
        else:
             print("Warning: A new client instance was created on the second call.")


        # --- Optional: Simple Test Call ---
        # Be mindful of API costs when uncommenting this section
        # print("\nAttempting a simple test call to the LLM...")
        # try:
        #     # Use invoke for simple calls with Langchain Expression Language (LCEL) style
        #     # Ensure langchain-core is installed if not already a dependency
        #     from langchain_core.prompts import ChatPromptTemplate
        #
        #     prompt = ChatPromptTemplate.from_messages([
        #         ("system", "You are a helpful assistant."),
        #         ("user", "{input}")
        #     ])
        #     chain = prompt | client # Chain the prompt and client
        #
        #     response = chain.invoke({"input": "In one short sentence, what is OpenRouter?"})
        #
        #     # The response object structure depends on the Langchain version
        #     # Usually response.content holds the text
        #     if hasattr(response, 'content'):
        #         print("\nTest call response:")
        #         print(response.content)
        #     else:
        #         print("\nTest call response (raw):")
        #         print(response)
        #
        # except ImportError:
        #      print("\nSkipping test call: langchain-core components not found.")
        # except Exception as call_error:
        #      print(f"\nError during test call: {call_error}")

    except (ValueError, RuntimeError) as e:
         print(f"\nTest failed during client initialization: {e}")
    except Exception as e:
         print(f"\nAn unexpected error occurred during testing: {e}")

    print("\n--- LLM Client Test Complete ---")