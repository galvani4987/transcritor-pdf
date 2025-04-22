# -*- coding: utf-8 -*-
"""
Unit tests for the src.output_handler.formatter module.
"""

import pytest # Import pytest framework
import os
# Import the function we want to test
from src.output_handler.formatter import format_output_for_rag, MIN_CHUNK_LENGTH

# --- Test Cases for format_output_for_rag ---

def test_format_output_for_rag_basic():
    """
    Tests basic functionality: chunking, metadata assignment, skipping short chunks.
    """
    sample_page_data_list = [
        { # Page 1 - multiple chunks, one short
            "page_number": 1,
            # CORRECTED: Made paragraphs longer than MIN_CHUNK_LENGTH (50)
            "extracted_text": "This is the first paragraph, and we need to make sure it is actually long enough to pass the minimum chunk length check.\n\n" + \
                              "This is the second paragraph, also made significantly longer to ensure it meets the criteria set by MIN_CHUNK_LENGTH.\n\n" + \
                              "Short.", # This chunk should still be skipped
            "client_name": "Test Client A",
            "document_date": "2025-01-01",
            "signature_found": True,
        },
        { # Page 2 - one valid chunk
            "page_number": 2,
            "extracted_text": "Single valid paragraph on page two, meeting minimum length criteria.",
            "client_name": "Test Client A",
            "document_date": "2025-01-01",
            "signature_found": False,
        },
        { # Page 3 - error page
            "page_number": 3,
            "error": "Some Error Occurred",
            "extracted_text": "Error processing this page",
        },
        { # Page 4 - no text
            "page_number": 4,
            "extracted_text": None,
        },
         { # Page 5 - empty text
            "page_number": 5,
            "extracted_text": "",
        }
    ]
    original_pdf_path = "/path/to/dummy/document.pdf"
    pdf_basename = os.path.basename(original_pdf_path)

    # Call the function under test
    rag_chunks = format_output_for_rag(sample_page_data_list, original_pdf_path)

    # --- Assertions ---
    # Expected number of chunks (2 from page 1, 1 from page 2)
    assert len(rag_chunks) == 3, f"Should generate 3 valid chunks, but got {len(rag_chunks)}"

    # Check first chunk (from page 1)
    chunk1 = rag_chunks[0]
    assert chunk1["chunk_id"] == f"{pdf_basename}_p1_c1"
    # CORRECTED: Check against the longer text
    assert chunk1["text_content"] == "This is the first paragraph, and we need to make sure it is actually long enough to pass the minimum chunk length check."
    assert chunk1["metadata"]["source_pdf"] == pdf_basename
    assert chunk1["metadata"]["page_number"] == 1
    assert chunk1["metadata"]["chunk_index_on_page"] == 1
    assert chunk1["metadata"]["client_name"] == "Test Client A"
    assert chunk1["metadata"]["document_date"] == "2025-01-01"
    assert chunk1["metadata"]["signature_found"] is True

    # Check second chunk (from page 1)
    chunk2 = rag_chunks[1]
    assert chunk2["chunk_id"] == f"{pdf_basename}_p1_c2" # Global counter continues
    # CORRECTED: Check against the longer text
    assert chunk2["text_content"] == "This is the second paragraph, also made significantly longer to ensure it meets the criteria set by MIN_CHUNK_LENGTH."
    assert chunk2["metadata"]["page_number"] == 1
    assert chunk2["metadata"]["chunk_index_on_page"] == 2 # Index within the page
    assert chunk2["metadata"]["client_name"] == "Test Client A"

    # Check third chunk (from page 2)
    chunk3 = rag_chunks[2]
    assert chunk3["chunk_id"] == f"{pdf_basename}_p2_c3" # Global counter increments
    assert chunk3["text_content"] == "Single valid paragraph on page two, meeting minimum length criteria."
    assert chunk3["metadata"]["page_number"] == 2
    assert chunk3["metadata"]["chunk_index_on_page"] == 1
    assert chunk3["metadata"]["signature_found"] is False

def test_format_output_for_rag_empty_input():
    """Tests behavior with empty input list."""
    rag_chunks = format_output_for_rag([], "/path/to/dummy.pdf")
    assert rag_chunks == [], "Should return empty list for empty input"

def test_format_output_for_rag_no_valid_text():
    """Tests behavior when no pages have valid text."""
    sample_page_data_list = [
        {"page_number": 1, "extracted_text": "Too short"},
        {"page_number": 2, "error": "Failed"},
        {"page_number": 3, "extracted_text": None},
    ]
    rag_chunks = format_output_for_rag(sample_page_data_list, "/path/to/dummy.pdf")
    assert rag_chunks == [], "Should return empty list if no valid text chunks found"