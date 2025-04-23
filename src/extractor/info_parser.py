# -*- coding: utf-8 -*-
"""Parses structured information (entities) from raw extracted text using an LLM.

This module takes the raw text output from the `text_extractor` module and
uses a separate LLM call, guided by a specific prompt, to identify and extract
predefined pieces of information (e.g., client name, document date, signature
presence, medical conditions). It leverages the configured Langchain client
and aims to return the extracted information in a structured JSON format.
Includes logging for operations and errors.
"""

import json
import sys
import logging # Import logging
from typing import Dict, Any, Optional
# Import LLM client getter
from .llm_client import get_llm_client # Assumes llm_client also uses logging
# Import Langchain components
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import PromptTemplate

# Get a logger instance for this module
logger = logging.getLogger(__name__)

# --- Output Parser ---
# Use Langchain's built-in JSON parser. It attempts to parse the LLM's
# string output as a JSON object. More robust parsing (e.g., handling
# malformed JSON) might require custom logic or different parsers.
parser = JsonOutputParser()

# --- Prompt Template String (Defined line by line to avoid formatting issues) ---
# Instruct the LLM to extract specific fields and return ONLY JSON.
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


# Create the prompt template object
prompt = PromptTemplate(
    template=prompt_template_str,
    input_variables=["extracted_text"],
    # partial_variables={"format_instructions": parser.get_format_instructions()} # If using PydanticOutputParser
)

# --- Parsing Function ---
def parse_extracted_info(raw_text: str) -> Optional[Dict[str, Any]]:
    """Parses structured information from raw text via an LLM call.

    Takes raw text, formats it into a prompt requesting JSON output containing
    specific fields (client_name, document_date, signature_found,
    relevant_illness_mentions), sends it to the configured LLM, and uses a
    JsonOutputParser to attempt converting the response into a Python dictionary.

    Args:
        raw_text: The raw text content extracted from a document page, intended
                  as input for the LLM analysis.

    Returns:
        A dictionary containing the parsed information with keys matching the
        prompt request if the LLM call and JSON parsing are successful.
        Returns None if the input text is invalid, the LLM call fails, or
        the LLM response cannot be parsed into the expected dictionary format.

    Raises:
        RuntimeError: If the LLM client cannot be initialized (propagated from
                      `get_llm_client`).
        Exception: For unexpected errors during the Langchain chain invocation
                   or parsing, although most are caught and logged, returning None.
                   Potentially raises exceptions from `get_llm_client`.
    """
    if not raw_text or not isinstance(raw_text, str):
        logger.warning("Info Parser: Invalid or empty input text provided. Skipping parsing.")
        return None

    logger.info("Starting structured information parsing from text...")
    # TODO: Consider adding text length limiting here if needed for cost/context window.
    # logger.debug(f"Input text length: {len(raw_text)}")

    try:
        # Obtain the configured LLM client instance
        llm = get_llm_client()

        # Construct the Langchain Expression Language (LCEL) chain
        # This defines the sequence: format prompt -> call LLM -> parse output
        chain = prompt | llm | parser
        logger.info("Sending text to LLM for structured parsing...")

        # Execute the chain with the input text
        parsed_result = chain.invoke({"extracted_text": raw_text})
        logger.info("LLM parsing call completed.")

        # --- Validate the parsed result ---
        if isinstance(parsed_result, dict):
            # Basic validation: check if it's a dictionary.
            # More robust validation could check for specific keys or value types.
            logger.debug(f"Parsed Info Dictionary: {parsed_result}")
            return parsed_result
        else:
            # Log an error if the parser didn't return a dictionary
            logger.error(f"JSON parser did not return a dictionary. "
                         f"Got type: {type(parsed_result)}. Output: {parsed_result}")
            return None

    except RuntimeError as e:
         # Catch client initialization errors specifically
         logger.error(f"LLM client runtime error during info parsing: {e}", exc_info=True)
         raise # Re-raise runtime errors as they are critical
    except Exception as e:
        # Catch other potential errors during the invoke/parse process
        logger.error(f"Error during structured information parsing: {e}", exc_info=True)
        # Return None to indicate parsing failure for this text
        return None

# --- Testing Block ---
if __name__ == "__main__":
    # Configure logging for test run
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(name)s - %(message)s')
    logger.info("--- Running info_parser.py directly for testing ---")
    # Requires .env file for LLM client configuration

    # Example raw text input
    test_raw_text = """
    ATESTADO MÉDICO

    Atesto, para os devidos fins, que o Sr. João Carlos da Silva, esteve sob meus
    cuidados médicos no dia 15 de Abril de 2025, apresentando quadro de forte
    gripe (Influenza H3N2) e sinusite aguda. Necessita de repouso por 5 dias.
    CID J10.1 + J01. São Luís, 15/04/2025
    _________________________
    Dr. Ricardo Mendes CRM-MA 9876
    """
    logger.info("\nInput Text:\n```\n" + test_raw_text + "\n```")

    try:
        # Attempt to parse the information using the function
        logger.info("Attempting to parse information (requires configured .env)...")
        parsed_data = parse_extracted_info(test_raw_text)

        if parsed_data:
            logger.info("--- Parsed Information (JSON) ---")
            # Pretty print the dictionary output using print for direct visibility
            print(json.dumps(parsed_data, indent=2, ensure_ascii=False))
            logger.info("---------------------------------")
        else:
            logger.warning("Information parsing failed or returned None.")

    except (RuntimeError, ValueError) as e:
        # Catch initialization errors if they occur during test
        logger.error(f"Testing failed due to configuration/initialization error: {e}")
    except Exception as e:
         # Catch any other unexpected errors during the test execution
         logger.error(f"An unexpected error occurred during testing: {e}", exc_info=True)

    logger.info("--- Info Parser Test Complete ---")