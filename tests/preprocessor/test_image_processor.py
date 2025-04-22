# -*- coding: utf-8 -*-
"""
Unit tests for the src.preprocessor.image_processor module.
"""

import pytest
import numpy as np
from PIL import Image
# Import the function to test
from src.preprocessor.image_processor import preprocess_image

# --- Test Cases for preprocess_image ---

def create_dummy_image(mode='RGB', size=(100, 50), color='white') -> Image.Image:
    """Helper function to create a simple PIL Image for testing."""
    return Image.new(mode, size, color)

def test_preprocess_image_runs_without_error():
    """
    Tests if preprocess_image runs without raising exceptions for a valid input image.
    """
    try:
        dummy_rgb = create_dummy_image(mode='RGB')
        processed_img = preprocess_image(dummy_rgb)
        # Basic check: Is the output a PIL Image?
        assert isinstance(processed_img, Image.Image)
        # Basic check: Is the output mode grayscale or binary as expected from the pipeline?
        # Our current pipeline ends with Sauvola binarization, which results in uint8 (0 or 255),
        # which PIL often represents as 'L' mode (grayscale) when converted back.
        # If we expected strictly binary '1' mode, the conversion back needs adjustment.
        # Let's accept 'L' for now, assuming the output is effectively binary 0/255.
        assert processed_img.mode == 'L', f"Expected mode 'L' (grayscale/binary) but got {processed_img.mode}"

    except Exception as e:
        pytest.fail(f"preprocess_image raised an exception unexpectedly: {e}")

def test_preprocess_image_handles_grayscale_input():
    """
    Tests if the function handles grayscale input correctly.
    """
    try:
        dummy_gray = create_dummy_image(mode='L') # Create grayscale image
        processed_img = preprocess_image(dummy_gray)
        assert isinstance(processed_img, Image.Image)
        # Should still output 'L' mode after processing
        assert processed_img.mode == 'L', f"Expected mode 'L' but got {processed_img.mode}"
    except Exception as e:
        pytest.fail(f"preprocess_image raised an exception on grayscale input: {e}")

def test_preprocess_image_wrong_input_type():
    """
    Tests if the function raises TypeError for non-PIL Image input.
    """
    with pytest.raises(TypeError):
        preprocess_image(np.zeros((10, 10), dtype=np.uint8)) # Pass NumPy array instead of PIL Image

# Add more tests later:
# - Test specific outputs of intermediate steps (if refactored)
# - Test with images containing actual noise/contrast issues (might need sample files)
# - Test edge cases (e.g., very small images)