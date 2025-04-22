# -*- coding: utf-8 -*-
"""
Module responsible for formatting the extracted page data into a structure
suitable for Retrieval-Augmented Generation (RAG) systems.

This typically involves creating text chunks and associating relevant metadata
(source file, page number, extracted entities) with each chunk.
"""

import json
import os
from typing import List, Dict, Any, Generator

# --- Configuration (Consider moving to a config file later) ---
# How to chunk the text? Simple splitting by paragraphs for now.
# More sophisticated methods (e.g., by sentence, fixed size with overlap)
# might be needed later using libraries like Langchain's text splitters.
CHUNK_SEPARATOR = "\n\n" # Split by double newline (paragraphs)

# Minimum chunk length to avoid very small, meaningless chunks
MIN_CHUNK_LENGTH = 50 # Characters

def format_output_for_rag(all_pages_data: List[Dict[str, Any]], original_pdf_path: str) -> List[Dict[str, Any]]:
    """
    Formats the collected data from all pages into a list of dictionaries,
    where each dictionary represents a text chunk suitable for RAG indexing.

    Args:
        all_pages_data: A list of dictionaries, where each dict contains the
                        extracted information for a single page (including
                        'page_number', 'extracted_text', 'client_name', etc.).
        original_pdf_path: The path to the original PDF file processed.

    Returns:
        A list of dictionaries, each representing a chunk with its text content
        and associated metadata. Returns an empty list if input is empty or
        no valid text is found.
    """
    print("\n--- Formatting output for RAG ---")
    rag_chunks = []
    chunk_id_counter = 0

    if not all_pages_data:
        print("  No page data provided to format.")
        return []

    for page_data in all_pages_data:
        page_number = page_data.get("page_number", "Unknown")
        extracted_text = page_data.get("extracted_text", "")

        # Skip pages with errors or no extracted text
        if not extracted_text or page_data.get("error"):
            print(f"  Skipping page {page_number} due to error or missing text.")
            continue

        # --- Basic Text Chunking (Example: by paragraph) ---
        # Replace this with more sophisticated chunking if needed later
        text_chunks = extracted_text.split(CHUNK_SEPARATOR)

        for i, chunk_text in enumerate(text_chunks):
            chunk_text = chunk_text.strip() # Remove leading/trailing whitespace

            # Skip empty or very short chunks
            if len(chunk_text) < MIN_CHUNK_LENGTH:
                continue

            chunk_id_counter += 1

            # --- Metadata Association ---
            # Collect relevant metadata for this chunk
            metadata = {
                "source_pdf": original_pdf_path,
                "page_number": page_number,
                "chunk_index_on_page": i + 1, # 1-based index of chunk within the page
                "client_name": page_data.get("client_name"), # Carry over parsed info
                "document_date": page_data.get("document_date"),
                "signature_found": page_data.get("signature_found"),
                # Add other relevant parsed info if available
                # "relevant_illness_mentions": page_data.get("relevant_illness_mentions"),
            }
            # Filter out metadata fields with None values if desired
            # metadata = {k: v for k, v in metadata.items() if v is not None}

            # --- Create RAG Chunk Dictionary ---
            rag_chunk_data = {
                "chunk_id": f"pdf_{os.path.basename(original_pdf_path)}_p{page_number}_c{chunk_id_counter}", # Unique ID
                "text_content": chunk_text,
                "metadata": metadata,
            }
            rag_chunks.append(rag_chunk_data)

    print(f"Formatted data into {len(rag_chunks)} chunks for RAG.")
    return rag_chunks

# Example usage block (for testing when script is run directly)
if __name__ == "__main__":
    print("\n--- Running formatter.py directly for testing ---")

    # Example input data (simulating output from previous steps)
    sample_page_data_list = [
        { # Page 1
            "page_number": 1,
            "source_file": "test_doc.pdf",
            "temp_image_path": "temp/page_001.webp",
            "preprocessing_applied": True,
            "extracted_text": "This is the first paragraph of page 1.\n\nThis is the second paragraph, which is a bit longer and contains some keywords like diabetes and hypertension.\n\nShort third para.",
            "client_name": "Maria Souza",
            "document_date": "2025-04-20",
            "signature_found": True,
            "relevant_illness_mentions": ["diabetes", "hypertension"]
        },
        { # Page 2 (with less text)
            "page_number": 2,
            "source_file": "test_doc.pdf",
            "temp_image_path": "temp/page_002.webp",
            "preprocessing_applied": True,
            "extracted_text": "Page 2 only has one single paragraph of text content which is long enough to be considered a chunk.",
            "client_name": "Maria Souza", # Assume name persists or is re-extracted
            "document_date": "2025-04-20", # Assume date persists
            "signature_found": False,
            "relevant_illness_mentions": []
        },
        { # Page 3 (with error)
            "page_number": 3,
            "source_file": "test_doc.pdf",
            "temp_image_path": "temp/page_003.webp",
            "error": "LLM Timeout",
            "extracted_text": "Processing Error"
        }
    ]
    sample_pdf_path = "example_docs/medical_report_01.pdf"

    print("\nInput Page Data (Sample):")
    # print(json.dumps(sample_page_data_list, indent=2)) # Can be long

    # Format the data
    formatted_chunks = format_output_for_rag(sample_page_data_list, sample_pdf_path)

    if formatted_chunks:
        print("\n--- Formatted Chunks for RAG (Sample Output) ---")
        # Print the first chunk as an example
        print("Example Chunk (First Chunk):")
        print(json.dumps(formatted_chunks[0], indent=2, ensure_ascii=False))
        print(f"\nTotal chunks generated: {len(formatted_chunks)}")
        print("-----------------------------------------------")
    else:
        print("\nNo RAG chunks were generated from the sample data.")

    print("\n--- Formatter Test Complete ---")