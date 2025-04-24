# -*- coding: utf-8 -*-
"""Parses structured information (entities) from raw extracted text using an LLM.
Defines the chain within the parsing function. Includes logging and specific
OpenAI API error handling.
"""

import json
import sys
import logging
from typing import Dict, Any, Optional
# Import LLM client getter
from .llm_client import get_llm_client
# Import Langchain components
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import PromptTemplate
# Import Langchain and OpenAI exceptions
from langchain_core.exceptions import OutputParserException
try:
    from openai import (
        APIError, APIConnectionError, APITimeoutError, AuthenticationError,
        BadRequestError, PermissionDeniedError, RateLimitError
    )
    OPENAI_ERRORS_AVAILABLE = True
except ImportError:
    OPENAI_ERRORS_AVAILABLE = False
    class APIError(Exception): pass
    class APIConnectionError(APIError): pass
    class APITimeoutError(APIError): pass
    class AuthenticationError(APIError): pass
    class BadRequestError(APIError): pass
    class PermissionDeniedError(APIError): pass
    class RateLimitError(APIError): pass
    logging.warning("openai library not found or exceptions changed. Specific API error handling may be limited.")

# Get a logger instance for this module
logger = logging.getLogger(__name__)

# --- Output Parser ---
parser = JsonOutputParser()

# --- Prompt Template String (Defined line by line) ---
prompt_lines = [
    "Analyze the following text extracted from a medical document page.",
    "Identify and extract the following information:",
    "- client_name: The patient's full name (null if none).",
    "- document_date: The document's date (YYYY-MM-DD if possible, else as written; null if none).",
    "- signature_found: Boolean (true/false) indicating if a professional signature is present/implied.",
    "- relevant_illness_mentions: List of strings with key medical conditions/symptoms (empty list [] if none).",
    "",
    "Return ONLY a valid JSON object with these exact keys. No explanations.",
    "",
    "Extracted Text:",
    "```text",
    "{extracted_text}",
    "```",
    "",
    "JSON Output:",
]
prompt_template_str = "\n".join(prompt_lines)

# Create the prompt template object at module level
prompt = PromptTemplate(
    template=prompt_template_str,
    input_variables=["extracted_text"],
)

# --- Parsing Function ---
def parse_extracted_info(raw_text: str) -> Optional[Dict[str, Any]]:
    """Parses structured information from raw text using an LLM call with error handling.

    Takes raw text, constructs an LCEL chain (Prompt | LLM | Parser),
    invokes it, and handles potential exceptions including specific OpenAI API errors.

    Args:
        raw_text: The raw text content extracted from a document page.

    Returns:
        A dictionary containing the parsed information if successful, otherwise None.

    Raises:
        RuntimeError: If the LLM client cannot be initialized or critical API errors occur.
    """
    if not raw_text or not isinstance(raw_text, str):
        logger.warning("Info Parser: Invalid or empty input text provided. Skipping parsing.")
        return None

    logger.info("Starting structured information parsing...")
    parsed_result = None
    try:
        # --- Get LLM Client ---
        llm = get_llm_client() # Can raise RuntimeError

        # --- Define the LCEL Chain INSIDE the function ---
        chain = prompt | llm | parser
        logger.debug("LCEL chain (prompt | llm | parser) constructed.")

        # --- Invoke the chain with specific error handling ---
        logger.info("Invoking information parsing chain...")
        try:
            parsed_result = chain.invoke({"extracted_text": raw_text})
            logger.info("Chain invocation successful.")

        # --- Specific OpenAI API Error Handling ---
        except AuthenticationError as e:
            logger.critical(f"OpenAI API Authentication Error during info parsing: {e}", exc_info=True)
            raise RuntimeError("API Authentication Failed during info parsing") from e
        except PermissionDeniedError as e:
             logger.critical(f"OpenAI API Permission Error during info parsing: {e}", exc_info=True)
             raise RuntimeError("API Permission Denied during info parsing") from e
        except RateLimitError as e:
            logger.error(f"OpenAI API Rate Limit Exceeded during info parsing: {e}", exc_info=True)
            return None # Fail for this page, maybe retry later
        except APITimeoutError as e:
             logger.error(f"OpenAI API Timeout Error during info parsing: {e}", exc_info=True)
             return None # Fail for this page, maybe retry later
        except APIConnectionError as e:
             logger.error(f"OpenAI API Connection Error during info parsing: {e}", exc_info=True)
             return None # Fail for this page, maybe retry later
        except BadRequestError as e:
             logger.error(f"OpenAI API Bad Request Error during info parsing: {e}", exc_info=True)
             return None # Input/prompt likely invalid
        except APIError as e: # Catch other OpenAI API errors (like 5xx)
             logger.error(f"OpenAI API Error during info parsing: {e}", exc_info=True)
             return None # Fail for this page, maybe retry later
        # --- Langchain Specific Error Handling ---
        except OutputParserException as ope:
            # Error parsing the LLM's response (e.g., not valid JSON)
            logger.error(f"Failed to parse LLM response as JSON: {ope}", exc_info=True)
            return None
        # --- End Specific Error Handling ---

        # --- Validate result type if no exception occurred ---
        if isinstance(parsed_result, dict):
            logger.debug(f"Parsed Info Dictionary: {parsed_result}")
            return parsed_result
        else:
            # This might happen if the LLM call succeeded but the parser returned an unexpected type
            logger.error(f"Chain returned unexpected type after invoke. Expected dict, got: {type(parsed_result)}. Result: {parsed_result}")
            return None

    except RuntimeError as rte:
         # Catch client initialization errors
         logger.critical(f"LLM client runtime error preventing info parsing: {rte}", exc_info=True)
         raise # Re-raise critical runtime errors
    except Exception as e:
        # Catch any other unexpected errors during setup or invocation
        logger.error(f"Unexpected error during structured information parsing setup/call: {e}", exc_info=True)
        return None

# No __main__ block needed as testing is done via pytest