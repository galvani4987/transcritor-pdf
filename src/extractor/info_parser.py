# -*- coding: utf-8 -*-
"""
Module for parsing structured information from raw extracted text using an LLM.
(Complete file created via Overwrite)
"""

import json
import sys
from typing import Dict, Any, Optional
# Import LLM client getter
from .llm_client import get_llm_client
# Import Langchain components
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import PromptTemplate

# --- Output Parser ---
# Use Langchain's built-in JSON parser
parser = JsonOutputParser()

# --- Prompt Template String (Defined line by line) ---
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
)

# --- Parsing Function ---
def parse_extracted_info(raw_text: str) -> Optional[Dict[str, Any]]:
    """
    Parses structured information from raw text using an LLM call.

    Args:
        raw_text: The raw text content extracted from a document page.

    Returns:
        A dictionary with parsed info, or None on failure/invalid input.
    """
    if not raw_text or not isinstance(raw_text, str):
        print("  Info Parser: Invalid input text.", file=sys.stderr)
        return None

    print("  Starting structured information parsing...")
    try:
        llm = get_llm_client()
        # Chain: Prompt -> LLM -> JSON Parser
        chain = prompt | llm | parser
        print("  Sending text to LLM for structured parsing...")
        # Provide the raw text as input
        parsed_result = chain.invoke({"extracted_text": raw_text})
        print("  LLM parsing successful.")

        # Basic validation of the result
        if isinstance(parsed_result, dict):
            # Add more robust validation if needed (e.g., check key existence)
            print(f"  Parsed Info: {parsed_result}")
            return parsed_result
        else:
            print(f"  Error: Parser did not return a dict. Got: {type(parsed_result)}", file=sys.stderr)
            return None

    except Exception as e:
        print(f"Error during structured information parsing: {e}", file=sys.stderr)
        return None

# --- Testing Block ---
if __name__ == "__main__":
    print("\n--- Running info_parser.py directly for testing ---")
    # Requires .env file for LLM client

    test_raw_text = """
    ATESTADO MÉDICO
    Atesto, para os devidos fins, que o Sr. João Carlos da Silva, esteve sob meus
    cuidados médicos no dia 15 de Abril de 2025, apresentando quadro de forte
    gripe (Influenza H3N2) e sinusite aguda. Necessita de repouso por 5 dias.
    CID J10.1 + J01. São Luís, 15/04/2025
    _________________________
    Dr. Ricardo Mendes CRM-MA 9876
    """
    print("\nInput Text:\n```\n" + test_raw_text + "\n```")

    try:
        parsed_data = parse_extracted_info(test_raw_text)
        if parsed_data:
            print("\n--- Parsed Information (JSON) ---")
            print(json.dumps(parsed_data, indent=2, ensure_ascii=False))
            print("---------------------------------")
        else:
            print("\nInformation parsing failed.")
    except Exception as e:
         print(f"\nTesting error: {e}")

    print("\n--- Info Parser Test Complete ---")