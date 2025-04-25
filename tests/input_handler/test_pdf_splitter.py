# -*- coding: utf-8 -*-
"""
Unit tests for the src.input_handler.pdf_splitter module.
Includes tests for per-page error handling.
"""

import pytest
import os
import shutil
from pathlib import Path
from unittest.mock import patch, MagicMock
# Import the function to test and related constants/types
from src.input_handler.pdf_splitter import split_pdf_to_pages, TEMP_PAGE_DIR, PageOutputType
# Import pypdfium2 to potentially create a dummy PDF for testing
try:
    import pypdfium2 as pdfium
    PYPDFIUM_AVAILABLE = True
except ImportError:
    PYPDFIUM_AVAILABLE = False
# Import PIL Image
from PIL import Image

# --- Test Setup / Teardown ---
@pytest.fixture(autouse=True)
def cleanup_temp_dir():
    """Cleans up the temporary directory before and after tests."""
    output_dir = Path(TEMP_PAGE_DIR)
    if output_dir.exists():
        shutil.rmtree(output_dir, ignore_errors=True)
    yield # Run the test
    if output_dir.exists():
        shutil.rmtree(output_dir, ignore_errors=True)

@pytest.fixture
def dummy_pdf(tmp_path) -> Path:
    """Fixture to create a dummy 2-page PDF file."""
    if not PYPDFIUM_AVAILABLE:
        pytest.skip("pypdfium2 not installed, cannot create test PDF.")

    pdf_path = tmp_path / "dummy_pdf_for_splitter_test.pdf"
    try:
        pdf = pdfium.PdfDocument.new()
        pdf.new_page(595, 842); pdf.new_page(595, 842) # Add 2 pages
        pdf.save(str(pdf_path))
        pdf.close()
        return pdf_path
    except Exception as e:
        pytest.fail(f"Failed to create dummy PDF for testing: {e}")

# --- Test Cases for split_pdf_to_pages ---

def test_split_pdf_non_existent_file():
    """
    Tests that FileNotFoundError is raised if the input PDF path does not exist.
    """
    non_existent_path = "path/that/does/not/exist/fake.pdf"
    with pytest.raises(FileNotFoundError):
        list(split_pdf_to_pages(non_existent_path))

@pytest.mark.skipif(not PYPDFIUM_AVAILABLE, reason="pypdfium2 not installed.")
def test_split_pdf_valid_pdf_produces_outputs(dummy_pdf):
    """
    Tests that splitting a valid PDF yields the correct number of non-None paths.
    """
    num_pages_expected = 2
    output_dir = Path(TEMP_PAGE_DIR)
    generated_items = []

    try:
        page_path_generator = split_pdf_to_pages(str(dummy_pdf))
        generated_items = list(page_path_generator)

        assert len(generated_items) == num_pages_expected, \
            f"Expected {num_pages_expected} items yielded, but got {len(generated_items)}"
        successful_paths = [p for p in generated_items if p is not None]
        assert len(successful_paths) == num_pages_expected, \
            f"Expected {num_pages_expected} successful paths, but got {len(successful_paths)}"

        for i, file_path_str in enumerate(successful_paths):
            file_path = Path(file_path_str)
            assert file_path.exists() # Check existence for the success case test
            assert file_path.is_file()
            assert file_path.parent.name == output_dir.name
            assert file_path.suffix.lower() == ".webp"
            assert file_path.stem.startswith(f"{dummy_pdf.stem}_page_")
    finally:
        pass # Cleanup handled by fixture

@pytest.mark.skipif(not PYPDFIUM_AVAILABLE, reason="pypdfium2 not installed.")
def test_split_pdf_handles_per_page_error(dummy_pdf, mocker):
    """
    Tests that the splitter yields None for a failed page and continues,
    yielding a path string for the successful page.
    """
    num_pages_total = 2
    generated_items = []

    # Mock page.render to fail on the first page
    render_call_count = 0
    mock_render = mocker.patch('pypdfium2._helpers.PdfPage.render')
    def render_side_effect(*args, **kwargs):
        nonlocal render_call_count
        render_call_count += 1
        if render_call_count == 1: # Fail on page 1
            raise pdfium.PdfiumError("Simulated rendering error for page 1")
        else: # Succeed on page 2
             mock_bitmap = MagicMock()
             mock_pil_image = MagicMock(spec=Image.Image)
             mock_pil_image.save = MagicMock() # Mock save method
             mock_bitmap.to_pil.return_value = mock_pil_image
             mock_bitmap.close = MagicMock()
             return mock_bitmap
    mock_render.side_effect = render_side_effect

    try:
        page_path_generator = split_pdf_to_pages(str(dummy_pdf))
        generated_items = list(page_path_generator)

        # Assertions
        assert len(generated_items) == num_pages_total
        # First item should be None (due to simulated render error)
        assert generated_items[0] is None, "Expected None for the first page"
        # Second item should be a valid path string
        assert isinstance(generated_items[1], str), "Expected a path string for the second page"
        # --- CORRECTION: Remove check for file existence as save was mocked ---
        # second_page_path = Path(generated_items[1])
        # assert second_page_path.exists(), f"Generated file for page 2 does not exist: {second_page_path}" # REMOVED
        # --- END CORRECTION ---
        # Optional: Check if the path string looks correct
        assert TEMP_PAGE_DIR in generated_items[1]
        assert generated_items[1].endswith(".webp")
        assert f"{dummy_pdf.stem}_page_0002" in generated_items[1]

    finally:
        pass # Cleanup handled by fixture

# TODO: Add tests for corrupted PDF (requires mocking PdfDocument or sample file)
# TODO: Add tests for password-protected PDF (requires mocking PdfDocument or sample file)