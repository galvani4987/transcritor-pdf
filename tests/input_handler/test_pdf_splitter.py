# -*- coding: utf-8 -*-
"""
Unit tests for the src.input_handler.pdf_splitter module.
"""

import pytest
import os
import shutil # For cleaning up test directories/files
from pathlib import Path # For easier path manipulation
# Import the function to test and related constants/types
from src.input_handler.pdf_splitter import split_pdf_to_pages, TEMP_PAGE_DIR, PageOutputType
# Import pypdfium2 to potentially create a dummy PDF for testing
try:
    import pypdfium2 as pdfium
    PYPDFIUM_AVAILABLE = True
except ImportError:
    PYPDFIUM_AVAILABLE = False

# --- Test Setup / Teardown (Optional Fixtures) ---
# We might use fixtures later to create/cleanup dummy files/dirs

# --- Test Cases for split_pdf_to_pages ---

def test_split_pdf_non_existent_file():
    """
    Tests that FileNotFoundError is raised if the input PDF path does not exist.
    """
    non_existent_path = "path/that/does/not/exist/fake.pdf"
    # Assert that calling the function with a bad path raises the expected error
    with pytest.raises(FileNotFoundError):
        # We need to consume the generator to trigger the exception
        list(split_pdf_to_pages(non_existent_path))

@pytest.mark.skipif(not PYPDFIUM_AVAILABLE, reason="pypdfium2 not installed, cannot create test PDF.")
def test_split_pdf_valid_pdf_produces_outputs(tmp_path):
    """
    Tests that splitting a valid (dummy) PDF yields the expected number of page paths.
    Uses pytest's tmp_path fixture for temporary file handling.
    """
    # --- Test Setup ---
    # 1. Create a dummy PDF file using pypdfium2 in the temporary directory
    dummy_pdf_path = tmp_path / "dummy_test.pdf"
    num_pages_expected = 2
    try:
        # Create a new PDF document
        pdf = pdfium.PdfDocument.new()
        # Add two blank pages (A4 size: 595x842 points)
        pdf.new_page(595, 842)
        pdf.new_page(595, 842)
        # Save the dummy PDF
        pdf.save(str(dummy_pdf_path))
        pdf.close()
    except Exception as e:
        pytest.fail(f"Failed to create dummy PDF for testing: {e}")

    # 2. Define the expected temporary output directory relative to project root
    #    (Note: pdf_splitter currently hardcodes TEMP_PAGE_DIR at root level)
    #    For isolated testing, ideally pdf_splitter would accept an output dir.
    #    Workaround: We'll check for files in the hardcoded TEMP_PAGE_DIR
    #    and clean it up manually.
    output_dir = Path(TEMP_PAGE_DIR)
    output_dir.mkdir(exist_ok=True) # Ensure it exists for cleanup later

    generated_files = []
    try:
        # --- Call the function under test ---
        page_path_generator = split_pdf_to_pages(str(dummy_pdf_path))
        generated_files = list(page_path_generator) # Consume the generator

        # --- Assertions ---
        assert len(generated_files) == num_pages_expected, \
            f"Expected {num_pages_expected} page files, but got {len(generated_files)}"

        # Check if the generated files actually exist and are in the expected dir
        for i, file_path_str in enumerate(generated_files):
            file_path = Path(file_path_str)
            assert file_path.exists(), f"Generated file path does not exist: {file_path}"
            assert file_path.is_file(), f"Generated path is not a file: {file_path}"
            # Check if it's inside the expected TEMP_PAGE_DIR
            assert file_path.parent.name == output_dir.name, \
                   f"File {file_path} not in expected directory {output_dir.name}"
            # Check extension (should be .webp)
            assert file_path.suffix.lower() == ".webp", \
                   f"Generated file has wrong extension: {file_path.suffix}"
            # Basic check for filename pattern (optional)
            assert file_path.stem.startswith("dummy_test_page_")

    finally:
        # --- Test Teardown ---
        # Clean up the generated temporary image files
        for file_path_str in generated_files:
            try:
                if os.path.exists(file_path_str):
                    os.remove(file_path_str)
            except OSError:
                pass # Ignore cleanup errors during test itself
        # Attempt to remove the TEMP_PAGE_DIR if empty
        try:
            if output_dir.exists() and not any(output_dir.iterdir()):
                output_dir.rmdir()
        except OSError:
             pass # Ignore cleanup errors

# TODO: Add tests for corrupted PDF (requires a sample corrupted file or mocking pypdfium2)
# TODO: Add tests for password-protected PDF (requires sample file or mocking)
# TODO: Add tests for different scales (if scale becomes configurable)