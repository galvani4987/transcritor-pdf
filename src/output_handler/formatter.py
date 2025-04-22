# -*- coding: utf-8 -*-
"""
Module responsible for formatting the extracted page data into a structure
suitable for Retrieval-Augmented Generation (RAG) systems. Includes logging.
"""

import json
import os # Needed for basename in chunk_id
import logging # Import logging
from typing import List, Dict, Any, Generator # Keep Generator if switching back later

# Get a logger instance for this module
logger = logging.getLogger(__name__)

# --- Configuration ---
CHUNK_SEPARATOR = "\n\n"
MIN_CHUNK_LENGTH = 50 # Characters

def format_output_for_rag(all_pages_data: List[Dict[str, Any]], original_pdf_path: str) -> List[Dict[str, Any]]:
    """
    Formats the collected data from all pages into a list of dictionaries,
    where each dictionary represents a text chunk suitable for RAG indexing.

    Args:
        all_pages_data: A list of dictionaries with extracted info per page.
        original_pdf_path: The path to the original PDF file processed.

    Returns:
        A list of dictionaries, each representing a chunk.
    """
    logger.info("--- Formatting output for RAG ---")
    rag_chunks = []
    chunk_id_counter = 0 # Global counter across all pages for unique chunk IDs

    if not all_pages_data:
        logger.warning("No page data provided to format.")
        return []

    pdf_basename = os.path.basename(original_pdf_path) # Get filename for chunk ID

    for page_data in all_pages_data:
        page_number = page_data.get("page_number", "Unknown")
        extracted_text = page_data.get("extracted_text", "")
        page_error = page_data.get("error") # Check if an error occurred on this page

        # Skip pages with errors or no valid extracted text
        if page_error or not extracted_text or extracted_text in ["Extraction Failed", "Processing Error", "Loading Error"]:
            logger.warning(f"Skipping page {page_number} due to error ('{page_error}') or missing/invalid text.")
            continue

        # --- Basic Text Chunking ---
        logger.debug(f"Chunking text for page {page_number}...")
        text_chunks = extracted_text.split(CHUNK_SEPARATOR)
        page_chunk_index = 0 # Reset chunk index for each page

        for chunk_text in text_chunks:
            chunk_text = chunk_text.strip()

            if len(chunk_text) < MIN_CHUNK_LENGTH:
                logger.debug(f"  Skipping short chunk on page {page_number}.")
                continue

            chunk_id_counter += 1
            page_chunk_index += 1

            # --- Metadata Association ---
            metadata = {
                "source_pdf": pdf_basename, # Store only filename, not full path? Or full path? Using basename for now.
                "page_number": page_number,
                "chunk_index_on_page": page_chunk_index,
                "client_name": page_data.get("client_name"),
                "document_date": page_data.get("document_date"),
                "signature_found": page_data.get("signature_found"),
                # Add illnesses list if available and not empty
                # "relevant_illness_mentions": page_data.get("relevant_illness_mentions") or [],
            }
            # Filter out metadata fields with None values before adding to chunk
            # metadata = {k: v for k, v in metadata.items() if v is not None}

            # --- Create RAG Chunk Dictionary ---
            rag_chunk_data = {
                # Create a more robust unique ID if needed
                "chunk_id": f"{pdf_basename}_p{page_number}_c{chunk_id_counter}",
                "text_content": chunk_text,
                "metadata": metadata,
            }
            rag_chunks.append(rag_chunk_data)
            logger.debug(f"  Created RAG chunk: {rag_chunk_data['chunk_id']}")

    logger.info(f"Formatted data into {len(rag_chunks)} chunks for RAG.")
    return rag_chunks

# Example usage block (for testing when script is run directly)
if __name__ == "__main__":
    # Configure logging for test run
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(name)s - %(message)s')
    logger.info("--- Running formatter.py directly for testing ---")

    # Example input data
    sample_page_data_list = [
        { # Page 1
            "page_number": 1, "source_file": "test_doc.pdf", "temp_image_path": "temp/page_001.webp",
            "preprocessing_applied": True,
            "extracted_text": "This is the first paragraph of page 1.\n\nThis is the second paragraph, which is a bit longer and contains some keywords like diabetes and hypertension.\n\nShort third para.",
            "client_name": "Maria Souza", "document_date": "2025-04-20", "signature_found": True,
            "relevant_illness_mentions": ["diabetes", "hypertension"]
        },
        { # Page 2
            "page_number": 2, "source_file": "test_doc.pdf", "temp_image_path": "temp/page_002.webp",
            "preprocessing_applied": True,
            "extracted_text": "Page 2 only has one single paragraph of text content which is long enough to be considered a chunk.",
            "client_name": "Maria Souza", "document_date": "2025-04-20", "signature_found": False,
            "relevant_illness_mentions": []
        },
        { # Page 3 (with error)
            "page_number": 3, "source_file": "test_doc.pdf", "temp_image_path": "temp/page_003.webp",
            "error": "LLM Timeout", "extracted_text": "Processing Error"
        }
    ]
    sample_pdf_path = "example_docs/medical_report_01.pdf"

    logger.info("\nInput Page Data (Sample):")
    # logger.debug(json.dumps(sample_page_data_list, indent=2)) # Log full input at debug if needed

    # Format the data
    formatted_chunks = format_output_for_rag(sample_page_data_list, sample_pdf_path)

    if formatted_chunks:
        logger.info("--- Formatted Chunks for RAG (Sample Output) ---")
        logger.info("Example Chunk (First Chunk):")
        # Use print for direct test output, or log the JSON string
        print(json.dumps(formatted_chunks[0], indent=2, ensure_ascii=False))
        logger.info(f"\nTotal chunks generated: {len(formatted_chunks)}")
        logger.info("-----------------------------------------------")
    else:
        logger.warning("No RAG chunks were generated from the sample data.")

    logger.info("--- Formatter Test Complete ---")