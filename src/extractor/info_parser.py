# -*- coding: utf-8 -*-
"""Parses structured information (entities) from raw extracted text using an LLM.
Defines the chain within the parsing function. Includes logging.
Removed the __main__ test block to avoid potential syntax errors during import.
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
# Import the exception for specific handling
from langchain_core.exceptions import OutputParserException

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
    """Parses structured information from raw text using an LLM call.

    Takes raw text, constructs an LCEL chain (Prompt | LLM | Parser),
    invokes it, and handles potential exceptions during invocation.

    Args:
        raw_text: The raw text content extracted from a document page.

    Returns:
        A dictionary containing the parsed information if successful,
        otherwise None.

    Raises:
        RuntimeError: If the LLM client cannot be initialized.
    """
    if not raw_text or not isinstance(raw_text, str):
        logger.warning("Info Parser: Invalid or empty input text provided. Skipping parsing.")
        return None

    logger.info("Starting structured information parsing...")
    try:
        # --- Get LLM Client ---
        llm = get_llm_client()

        # --- Define the LCEL Chain INSIDE the function ---
        chain = prompt | llm | parser
        logger.debug("LCEL chain (prompt | llm | parser) constructed.")

        # --- Invoke the chain ---
        logger.info("Invoking information parsing chain...")
        parsed_result = chain.invoke({"extracted_text": raw_text})
        logger.info("Chain invocation successful.")

        # Basic validation
        if isinstance(parsed_result, dict):
            logger.debug(f"Parsed Info Dictionary: {parsed_result}")
            return parsed_result
        else:
            logger.error(f"Chain returned unexpected type. Expected dict, got: {type(parsed_result)}. Result: {parsed_result}")
            return None

    except OutputParserException as ope:
        logger.error(f"Failed to parse LLM response as JSON: {ope}", exc_info=True)
        return None
    except RuntimeError as rte:
         logger.critical(f"LLM client runtime error during info parsing: {rte}", exc_info=True)
         raise
    except Exception as e:
        logger.error(f"Error during structured information parsing chain invocation: {e}", exc_info=True)
        return None

# No __main__ block below this line