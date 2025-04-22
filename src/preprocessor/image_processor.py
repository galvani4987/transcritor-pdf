# -*- coding: utf-8 -*-
"""
Module for preprocessing individual page images before OCR/extraction.

Applies techniques based on research findings (Grayscale, Median Filter,
CLAHE, Sauvola Binarization) primarily using Scikit-image. Includes logging.
"""

from PIL import Image
import numpy as np
import sys
import os
import logging # Import logging

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
    # from skimage.transform import rotate, hough_line, hough_line_peaks # For Deskewing
    # from skimage.feature import canny # For Deskewing
except ImportError:
    logger.critical("scikit-image library not found. Please install it using: pip install scikit-image")
    # Exit if critical dependency is missing at import time
    sys.exit(1)

def preprocess_image(img_pil: Image.Image) -> Image.Image:
    """
    Applies a preprocessing pipeline to a PIL Image object using Scikit-image.

    Pipeline: [Deskew (TODO)] -> Grayscale -> Median -> CLAHE -> Sauvola -> [Crop (TODO)]

    Args:
        img_pil: The input PIL Image object.

    Returns:
        A new PIL Image object with preprocessing applied.
    """
    if not isinstance(img_pil, Image.Image):
        raise TypeError("Input must be a PIL Image object.")

    logger.info(f"Preprocessing image (mode: {img_pil.mode}, size: {img_pil.size})...")

    # --- Convert PIL Image to NumPy array ---
    try:
        img_array = np.array(img_pil)
        if img_array.ndim == 3 and img_array.shape[2] == 4: # RGBA
             logger.debug("Detected RGBA image, converting to RGB first.")
             img_array = img_array[:, :, :3]
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
            processed_img = rgb2gray(processed_img)
            logger.debug(f"Converted to grayscale (shape: {processed_img.shape}, dtype: {processed_img.dtype}).")
        except Exception as e:
             logger.warning(f"Failed to convert to grayscale: {e}", exc_info=True)
             # Attempt to continue if possible, maybe image was already grayscale-like?
    elif processed_img.dtype != np.float64 and processed_img.dtype != np.float32:
        processed_img = img_as_float(processed_img) # Ensure float if already single channel


    # --- Step 3: Median Filter (Noise Reduction) ---
    logger.debug("Applying Median Filter...")
    try:
        # Convert to uint8 for median filter, then back to float
        with np.errstate(invalid='ignore'): # Suppress potential warnings during conversion
            img_uint8 = img_as_ubyte(processed_img)
        processed_img_median = median(img_uint8, footprint=disk(1)) # Use footprint for skimage < 0.19, selem otherwise
        processed_img = img_as_float(processed_img_median)
        logger.debug("Applied Median Filter.")
    except Exception as e:
        logger.warning(f"Failed to apply Median Filter: {e}", exc_info=True)
        # Continue with the image before median filter if it fails

    # --- Step 4: CLAHE (Contrast Enhancement) ---
    logger.debug("Applying CLAHE...")
    try:
        # Parameters might need tuning
        processed_img = equalize_adapthist(processed_img, clip_limit=0.01)
        logger.debug("Applied CLAHE.")
    except Exception as e:
        logger.warning(f"Failed to apply CLAHE: {e}", exc_info=True)
        # Continue with the image before CLAHE if it fails

    # --- Step 5: Binarization (Sauvola) ---
    logger.debug("Applying Sauvola Binarization...")
    try:
        # Parameters might need tuning
        window_size = 15
        k = 0.2
        thresh_sauvola = threshold_sauvola(processed_img, window_size=window_size, k=k)
        binary_sauvola = processed_img > thresh_sauvola
        # Convert boolean array to uint8 (0 or 255) for PIL
        processed_img = img_as_ubyte(binary_sauvola)
        logger.debug(f"Applied Sauvola Binarization (window={window_size}, k={k}). Output is uint8 binary.")
    except Exception as e:
        logger.warning(f"Failed to apply Sauvola Binarization: {e}", exc_info=True)
        # Fallback: attempt simple thresholding if Sauvola fails? Or return grayscale?
        # For now, convert whatever we have to uint8 for consistency before returning PIL image
        if processed_img.dtype != np.uint8:
             logger.warning("Binarization failed, attempting fallback conversion to uint8.")
             try:
                 # Normalize if still float [0,1] before converting
                 if np.max(processed_img) <= 1.0 and np.min(processed_img) >= 0.0:
                     processed_img = img_as_ubyte(processed_img > 0.5) # Simple threshold at 0.5
                 else: # If range is unknown, just cast type (might be incorrect)
                      processed_img = processed_img.astype(np.uint8)
             except Exception as fallback_e:
                  logger.error(f"Fallback uint8 conversion also failed: {fallback_e}", exc_info=True)
                  # If even fallback fails, we might have to raise or return None


    # --- Step 6: [Placeholder] Cropping ---
    logger.debug("Skipping Cropping (Placeholder).")
    # TODO: Implement cropping

    # --- Convert final NumPy array back to PIL Image ---
    logger.debug(f"Converting final NumPy array (shape: {processed_img.shape}, dtype: {processed_img.dtype}) back to PIL Image...")
    try:
        # Ensure uint8 format for PIL
        if processed_img.dtype != np.uint8:
            logger.error(f"Final image array is not uint8 ({processed_img.dtype}) before PIL conversion!")
            # Attempt last-ditch conversion, though it might indicate earlier failure
            processed_img_final = img_as_ubyte(processed_img)
        else:
            processed_img_final = processed_img

        final_pil_image = Image.fromarray(processed_img_final)
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
    test_image_path = os.path.join(test_image_dir, "test_loader_image.webp")
    processed_image_path = os.path.join(test_image_dir, "processed_skimage_test_image.png")

    if os.path.exists(test_image_path):
        logger.info(f"Loading test image: {test_image_path}")
        input_image = None
        processed_image = None
        try:
            input_image = Image.open(test_image_path)
            input_image.load()
            logger.info(f"Input image loaded: mode={input_image.mode}, size={input_image.size}")

            processed_image = preprocess_image(input_image)

            logger.info(f"Saving processed image to: {processed_image_path}")
            processed_image.save(processed_image_path, format="PNG")

            logger.info(f"Test processing complete. Check the output image: {processed_image_path}")

        except FileNotFoundError:
             logger.error(f"Test image not found at {test_image_path}")
        except ImportError:
             # Already handled by critical log at top, but good practice here too
             logger.error("scikit-image not installed. Cannot run test.")
        except Exception as e:
             logger.error(f"An error occurred during testing: {e}", exc_info=True)
        finally:
            if input_image: input_image.close()
            if processed_image: processed_image.close()
            logger.info(f"(Remember to manually clean up '{test_image_dir}' directory if needed)")

    else:
        logger.warning(f"Test image not found at '{test_image_path}'.")
        logger.warning("Please ensure the test image exists (e.g., by running the loader.py test first)")
        logger.warning("or update the 'test_image_path' variable in this script.")

    logger.info("--- Image Processor Test Complete ---")