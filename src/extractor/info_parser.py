# -*- coding: utf-8 -*-
"""Parses structured information (entities) from raw extracted text using an LLM.
Defines the chain within the parsing function. Includes logging and specific
OpenAI API error handling. Uses refined prompt.
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

# --- Prompt Template String (Refined Version) ---
# Defined line by line to avoid formatting issues
prompt_lines = [
    "Analyze the following text, which was automatically extracted from a scanned page of a handwritten medical document and may contain OCR errors.",
    "Carefully identify and extract the following specific pieces of information:",
    "",
    '1.  **client_name**: The full name of the patient. Look for labels like "Paciente:" or "Nome:", or identify the name usually mentioned near the top/beginning of the document. Distinguish it from the doctor\'s name, which often appears at the end near the signature. If no patient name is clearly identifiable, return null.',
    '2.  **document_date**: The date the document was issued or signed. Look for dates in DD-MM-AA or DD-MM-AAAA format. Normalize any valid date found to the **DD-MM-AAAA** format. If multiple dates exist, prefer the main date of the document (often near the location or signature). If no date is clearly identifiable, return null.',
    '3.  **signature_found**: Return `true` if you find evidence of a professional signature (e.g., a doctor\'s name followed by "CRM", "CRO", "COREN", etc., or text indicating an electronic/digital signature, or a clearly demarcated signature area, typically at the bottom). Otherwise, return `false`.',
    '4.  **relevant_illness_mentions**: Create a list of all specific medical terms mentioned in the text that indicate a disease, illness, condition, diagnosis, significant symptom, or abnormality (e.g., "Faringite Aguda", "diabetes", "hipertensão", "CID J02.9", "febre", "lesão"). Do *not* include terms indicating normality (e.g., "sem alterações", "normal", "ausência de lesões"). If no such terms indicating abnormality are found, return an empty list `[]`.',
    "",
    "**Output Format:** Return ONLY a valid JSON object containing these exact keys (`client_name`, `document_date`, `signature_found`, `relevant_illness_mentions`). Do not include any explanations, introductory text, or markdown formatting around the JSON object.",
    "",
    "**Extracted Text:**",
    "```text",
    "{extracted_text}",
    "```",
    "",
    "**JSON Output:**",
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
        A dictionary containing the parsed information if successful,
        otherwise None.

    Raises:
        RuntimeError: If the LLM client cannot be initialized or critical API errors occur.
    """
    if not raw_text or not isinstance(raw_text, str):
        logger.warning("Info Parser: Invalid or empty input text provided. Skipping parsing.")
        return None

    logger.info("Starting structured information parsing...")
    parsed_result = None
    try:
        llm = get_llm_client()
        chain = prompt | llm | parser
        logger.debug("LCEL chain (prompt | llm | parser) constructed.")
        logger.info("Invoking information parsing chain...")
        try:
            parsed_result = chain.invoke({"extracted_text": raw_text})
            logger.info("Chain invocation successful.")
        except AuthenticationError as e:
            logger.critical(f"OpenAI API Authentication Error during info parsing: {e}", exc_info=True)
            raise RuntimeError("API Authentication Failed during info parsing") from e
        except PermissionDeniedError as e:
             logger.critical(f"OpenAI API Permission Error during info parsing: {e}", exc_info=True)
             raise RuntimeError("API Permission Denied during info parsing") from e
        except RateLimitError as e:
            logger.error(f"OpenAI API Rate Limit Exceeded during info parsing: {e}", exc_info=True)
            return None
        except APITimeoutError as e:
             logger.error(f"OpenAI API Timeout Error during info parsing: {e}", exc_info=True)
             return None
        except APIConnectionError as e:
             logger.error(f"OpenAI API Connection Error during info parsing: {e}", exc_info=True)
             return None
        except BadRequestError as e:
             logger.error(f"OpenAI API Bad Request Error during info parsing: {e}", exc_info=True)
             return None
        except APIError as e:
             logger.error(f"OpenAI API Error during info parsing: {e}", exc_info=True)
             return None
        except OutputParserException as ope:
            logger.error(f"Failed to parse LLM response as JSON: {ope}", exc_info=True)
            return None

        if isinstance(parsed_result, dict):
            logger.debug(f"Parsed Info Dictionary: {parsed_result}")
            return parsed_result
        else:
            logger.error(f"Chain returned unexpected type after invoke. Expected dict, got: {type(parsed_result)}. Result: {parsed_result}")
            return None

    except RuntimeError as rte:
         logger.critical(f"LLM client runtime error preventing info parsing: {rte}", exc_info=True)
         raise
    except Exception as e:
        logger.error(f"Unexpected error during structured information parsing setup/call: {e}", exc_info=True)
        return None

# No __main__ block