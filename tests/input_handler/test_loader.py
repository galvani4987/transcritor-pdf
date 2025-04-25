# -*- coding: utf-8 -*-
"""
Unit tests for the src.input_handler.loader module.
"""

import pytest
import os
import shutil
from pathlib import Path
from PIL import Image, UnidentifiedImageError
# Import the function to test
from src.input_handler.loader import load_page_image

# --- Test Setup / Teardown ---
TEST_DIR = Path("temp_test_loader_dir")

@pytest.fixture(scope="module", autouse=True)
def setup_teardown_test_dir():
    """Creates and cleans up a temporary directory for test files."""
    TEST_DIR.mkdir(exist_ok=True)
    yield # Run tests in the module
    shutil.rmtree(TEST_DIR, ignore_errors=True)

@pytest.fixture
def valid_image_path() -> Path:
    """Creates a valid dummy WebP image file and returns its path."""
    img_path = TEST_DIR / "valid_image.webp"
    try:
        dummy_img = Image.new('RGB', (20, 10), color = 'green')
        dummy_img.save(img_path, "webp", lossless=True)
        dummy_img.close()
    except Exception as e:
        pytest.fail(f"Failed to create valid test image: {e}")
    return img_path

@pytest.fixture
def invalid_image_path() -> Path:
    """Creates a text file (invalid image) and returns its path."""
    txt_path = TEST_DIR / "invalid_image.txt"
    try:
        with open(txt_path, "w") as f:
            f.write("This is not an image file.")
    except Exception as e:
        pytest.fail(f"Failed to create invalid test file: {e}")
    return txt_path

# --- Test Cases for load_page_image ---

def test_load_page_image_success(valid_image_path):
    """Tests loading a valid image file successfully."""
    loaded_image = None
    try:
        loaded_image = load_page_image(str(valid_image_path))
        assert isinstance(loaded_image, Image.Image), "Should return a PIL Image object"
        # Check some basic properties
        assert loaded_image.size == (20, 10)
        assert loaded_image.mode == 'RGB' # WebP lossless preserves mode
    finally:
        if loaded_image:
            loaded_image.close()

def test_load_page_image_non_existent_file():
    """Tests that FileNotFoundError is raised for a non-existent path."""
    non_existent_path = TEST_DIR / "i_do_not_exist.webp"
    with pytest.raises(FileNotFoundError):
        load_page_image(str(non_existent_path))

def test_load_page_image_invalid_image_file(invalid_image_path):
    """Tests that UnidentifiedImageError is raised for a non-image file."""
    with pytest.raises(UnidentifiedImageError):
        load_page_image(str(invalid_image_path))

def test_load_page_image_directory_path():
    """Tests that FileNotFoundError (or similar OS error) is raised for a directory path."""
    # Expect FileNotFoundError on Linux/macOS, maybe IsADirectoryError or PermissionError on Windows?
    # FileNotFoundError is raised by os.path.isfile check.
    with pytest.raises(FileNotFoundError):
         load_page_image(str(TEST_DIR)) # Pass the directory itself

def test_load_page_image_invalid_input_type():
    """Tests that TypeError is raised for non-string input."""
    with pytest.raises(TypeError):
        load_page_image(123) # type: ignore
    with pytest.raises(TypeError):
        load_page_image(None) # type: ignore
    with pytest.raises(TypeError):
        load_page_image(["path"]) # type: ignore