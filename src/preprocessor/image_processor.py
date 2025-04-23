# -*- coding: utf-8 -*-
"""Handles image preprocessing operations before OCR/extraction.

This module applies a sequence of image processing techniques, primarily
using the Scikit-image library, to enhance the quality and readability of
individual page images, especially those containing handwritten text from
scanned medical documents. The goal is to improve the accuracy of downstream
text extraction (OCR/LLM). Includes logging for operations and errors.
"""

from PIL import Image
import numpy as np
import sys
import os
import logging

# Get a logger instance for this module
logger = logging.getLogger(__name__)

# Import necessary functions from Scikit-image
try:
    from skimage import io as skimage_io
    from skimage.color import rgb2gray
    from skimage.filters import median, threshold_sauvola
    from skimage.morphology import disk
    from skimage.exposure import equalize_adapthist # CLAHE
    from skimage.util import img_as_ubyte, img_as_float
    # from skimage.transform import rotate # For Deskewing
except ImportError:
    logger.critical("scikit-image library not found. Please install it using: pip install scikit-image")
    sys.exit(1)

def preprocess_image(img_pil: Image.Image) -> Image.Image:
    """Applies a preprocessing pipeline to a PIL Image object using Scikit-image.

    The pipeline aims to improve image quality for OCR/LLM text extraction,
    particularly for scanned handwritten documents. The current pipeline is:
    1. Convert to Grayscale (if needed).
    2. Apply Median Filter for noise reduction.
    3. Apply CLAHE for adaptive contrast enhancement.
    4. Apply Sauvola adaptive binarization.
    (Placeholders remain for Deskewing and Cropping).

    Args:
        img_pil: The input PIL Image object, typically loaded from a temporary
                 page file (e.g., WebP).

    Returns:
        A new PIL Image object representing the processed image. The output
        image is typically binary (black and white text on background) but
        represented in 'L' mode (8-bit grayscale) by PIL after conversion
        from the boolean NumPy array.

    Raises:
        TypeError: If the input `img_pil` is not a PIL Image object.
        ImportError: If scikit-image is not installed (checked at module level).
        Exception: For various errors during image conversion (NumPy/PIL),
                   filtering, or binarization steps (e.g., memory errors,
                   invalid image data after intermediate steps).
    """
    if not isinstance(img_pil, Image.Image):
        msg = "Invalid input type for preprocess_image: Expected PIL Image."
        logger.error(msg)
        raise TypeError(msg)

    logger.info(f"Preprocessing image (mode: {img_pil.mode}, size: {img_pil.size})...")

    # --- Convert PIL Image to NumPy array ---
    try:
        img_array = np.array(img_pil)
        if img_array.ndim == 3 and img_array.shape[2] == 4: # RGBA
             logger.debug("Detected RGBA image, converting to RGB first.")
             img_array = img_array[:, :, :3]
        # Use img_as_float for skimage functions expecting values in [0, 1]
        img_float = img_as_float(img_array)
        logger.debug(f"Converted PIL image to NumPy array (shape: {img_float.shape}, dtype: {img_float.dtype}).")
    except Exception as e:
        logger.error(f"Error converting PIL image to NumPy array: {e}", exc_info=True)
        raise # Re-raise critical error

    processed_img = img_float

    # --- Step 1: [Placeholder] Deskewing ---
    logger.debug("Skipping Deskewing (Placeholder).")
    # TODO: Implement deskewing

    # --- Step 2: Convert to Grayscale ---
    if processed_img.ndim == 3:
        logger.debug("Converting to grayscale...")
        try:
            processed_img = rgb2gray(processed_img) # Outputs float64 in [0, 1]
            logger.debug(f"Converted to grayscale (shape: {processed_img.shape}, dtype: {processed_img.dtype}).")
        except Exception as e:
             logger.warning(f"Failed to convert to grayscale: {e}", exc_info=True)
             # Continue if possible
    elif processed_img.dtype != np.float64 and processed_img.dtype != np.float32:
        # Ensure float if already single channel but not float
        processed_img = img_as_float(processed_img)
        logger.debug("Input was single channel, ensured float type.")


    # --- Step 3: Median Filter (Noise Reduction) ---
    logger.debug("Applying Median Filter...")
    try:
        # median function might prefer uint8/uint16 depending on version
        # Convert to uint8, apply filter, convert back to float for next step
        with np.errstate(invalid='ignore'): # Suppress potential precision warnings
            img_uint8_med = img_as_ubyte(processed_img)
        # Use footprint/selem based on skimage version if needed, disk(1) is common
        processed_img_median = median(img_uint8_med, footprint=disk(1))
        processed_img = img_as_float(processed_img_median) # Back to float for CLAHE
        logger.debug("Applied Median Filter.")
    except Exception as e:
        logger.warning(f"Failed to apply Median Filter: {e}", exc_info=True)
        # Continue with the image before median filter

    # --- Step 4: CLAHE (Contrast Enhancement) ---
    logger.debug("Applying CLAHE...")
    try:
        # equalize_adapthist works directly on float images [0, 1]
        processed_img = equalize_adapthist(processed_img, clip_limit=0.01) # Tune clip_limit
        logger.debug("Applied CLAHE.")
    except Exception as e:
        logger.warning(f"Failed to apply CLAHE: {e}", exc_info=True)
        # Continue with the image before CLAHE

    # --- Step 5: Binarization (Sauvola) ---
    logger.debug("Applying Sauvola Binarization...")
    try:
        # Sauvola works on grayscale images (float or int)
        # Parameters require tuning based on image characteristics
        window_size = 15 # Must be odd
        k = 0.2
        # Ensure input is float for threshold_sauvola if not already
        if processed_img.dtype != np.float64 and processed_img.dtype != np.float32:
            processed_img_float_bin = img_as_float(processed_img)
        else:
            processed_img_float_bin = processed_img

        thresh_sauvola = threshold_sauvola(processed_img_float_bin, window_size=window_size, k=k)
        # Result is boolean array (True where pixel > threshold)
        binary_sauvola = processed_img_float_bin > thresh_sauvola
        # Convert boolean array to uint8 (0/255) for standard image format
        processed_img = img_as_ubyte(binary_sauvola)
        logger.debug(f"Applied Sauvola Binarization (window={window_size}, k={k}). Output is uint8 binary.")
    except Exception as e:
        logger.warning(f"Failed to apply Sauvola Binarization: {e}", exc_info=True)
        # Fallback strategy if binarization fails
        if processed_img.dtype != np.uint8:
             logger.warning("Binarization failed, attempting fallback conversion to uint8.")
             try:
                 # If still float [0,1], simple threshold; otherwise just cast
                 if np.max(processed_img) <= 1.0 and np.min(processed_img) >= 0.0:
                     processed_img = img_as_ubyte(processed_img > 0.5)
                 else:
                      processed_img = processed_img.astype(np.uint8)
             except Exception as fallback_e:
                  logger.error(f"Fallback uint8 conversion also failed: {fallback_e}", exc_info=True)
                  # If conversion fails, re-raise to signal critical issue
                  raise Exception("Failed to convert processed image to uint8") from fallback_e


    # --- Step 6: [Placeholder] Cropping ---
    logger.debug("Skipping Cropping (Placeholder).")
    # TODO: Implement cropping

    # --- Convert final NumPy array back to PIL Image ---
    logger.debug(f"Converting final NumPy array (shape: {processed_img.shape}, dtype: {processed_img.dtype}) back to PIL Image...")
    try:
        # Ensure the array is uint8 before converting to PIL
        if processed_img.dtype != np.uint8:
            # This should ideally not happen if fallback worked, but double-check
            logger.error(f"Final image array is not uint8 ({processed_img.dtype}) before PIL conversion!")
            processed_img_final = img_as_ubyte(processed_img) # Attempt conversion
        else:
            processed_img_final = processed_img

        # Create PIL Image from the uint8 NumPy array
        final_pil_image = Image.fromarray(processed_img_final)
        # The mode will likely be 'L' (8-bit grayscale) even for binary (0/255) data
        logger.info(f"Preprocessing complete. Final PIL Image mode: {final_pil_image.mode}")
        return final_pil_image
    except Exception as e:
        logger.error(f"Error converting final NumPy array to PIL Image: {e}", exc_info=True)
        raise # Re-raise critical error during final conversion

# Example usage block (for testing when script is run directly)
if __name__ == "__main__":
    # Configure logging specifically for the test run if needed
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(name)s - %(message)s')
    logger.info("--- Running image_processor.py directly for testing ---")

    test_image_dir = "temp_test_loader"
    # Use the original dummy image for testing the full pipeline
    test_image_path = os.path.join(test_image_dir, "test_loader_image.webp")
    processed_image_path = os.path.join(test_image_dir, "processed_skimage_test_image.png") # Save output here

    if os.path.exists(test_image_path):
        logger.info(f"Loading test image: {test_image_path}")
        input_image = None
        processed_image = None
        try:
            input_image = Image.open(test_image_path)
            input_image.load()
            logger.info(f"Input image loaded: mode={input_image.mode}, size={input_image.size}")

            # Apply preprocessing using the updated function
            processed_image = preprocess_image(input_image)

            # Save the processed image for visual inspection
            logger.info(f"Saving processed image to: {processed_image_path}")
            processed_image.save(processed_image_path, format="PNG") # Save as PNG for easy viewing

            logger.info(f"Test processing complete. Check the output image: {processed_image_path}")

        except FileNotFoundError:
             logger.error(f"Test image not found at {test_image_path}")
        except ImportError:
             # Should be caught at top level import, but good practice
             logger.error("scikit-image not installed. Cannot run test.")
        except Exception as e:
             logger.error(f"An error occurred during testing: {e}", exc_info=True)
        finally:
            # Close images if they were opened
            if input_image: input_image.close()
            if processed_image: processed_image.close()
            logger.info(f"(Remember to manually clean up '{test_image_dir}' directory if needed)")

    else:
        logger.warning(f"Test image not found at '{test_image_path}'.")
        logger.warning("Please ensure the test image exists (e.g., by running the loader.py test first)")
        logger.warning("or update the 'test_image_path' variable in this script.")

    logger.info("--- Image Processor Test Complete ---")