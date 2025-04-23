# -*- coding: utf-8 -*-
"""Handles image preprocessing operations before OCR/extraction.

Includes Deskewing based on Hough Transform.
"""

from PIL import Image
import numpy as np
import sys
import os
import logging
import math # For angle calculations

# Get a logger instance for this module
logger = logging.getLogger(__name__)

# Import necessary functions from Scikit-image
try:
    from skimage import io as skimage_io
    from skimage.color import rgb2gray
    from skimage.filters import median, threshold_sauvola, gaussian # Gaussian for Canny pre-smoothing
    from skimage.morphology import disk
    from skimage.exposure import equalize_adapthist # CLAHE
    from skimage.util import img_as_ubyte, img_as_float
    # Imports for Deskewing
    from skimage.feature import canny
    from skimage.transform import hough_line, hough_line_peaks, rotate
except ImportError:
    logger.critical("scikit-image library not found. Please install it using: pip install scikit-image")
    sys.exit(1)

# --- Helper Function for Deskewing ---
def estimate_skew_angle(image_gray: np.ndarray, angle_range: tuple = (-15, 15), num_peaks: int = 20) -> float:
    """Estimates the skew angle of text in a grayscale image using Hough transform.

    Args:
        image_gray: Grayscale input image (NumPy array, float or int).
        angle_range: Tuple defining the min and max angles (in degrees) to consider.
                     Defaults to (-15, 15) to focus on typical document skew.
        num_peaks: The number of peaks to extract from the Hough accumulator.

    Returns:
        The estimated skew angle in degrees. Returns 0.0 if no significant
        angle is detected or if an error occurs.
    """
    logger.debug("Estimating skew angle...")
    # Ensure image is float for processing consistency if needed
    image_float = img_as_float(image_gray)

    # 1. Edge Detection (Canny)
    # Apply slight Gaussian blur before Canny to reduce noise sensitivity
    sigma = 1.0 # Adjust sigma as needed
    blurred = gaussian(image_float, sigma=sigma)
    # Canny edge detection - thresholds might need tuning
    edges = canny(blurred, sigma=1.0, low_threshold=0.1, high_threshold=0.3) # Example thresholds

    # 2. Hough Transform
    # Define angles to test around 0 degrees and +/- 90 degrees
    # Restrict angles to a plausible range to avoid detecting vertical lines as skew
    min_angle_rad = np.deg2rad(angle_range[0])
    max_angle_rad = np.deg2rad(angle_range[1])
    # Test angles within the specified range around horizontal
    tested_angles = np.linspace(min_angle_rad, max_angle_rad, 180, endpoint=False) # Test 180 angles in range

    try:
        h, theta, d = hough_line(edges, theta=tested_angles)
    except Exception as e:
        logger.warning(f"Hough transform failed: {e}", exc_info=True)
        return 0.0 # Return 0 angle if Hough fails

    # 3. Find Peaks in Hough Space
    try:
        # Find the most prominent lines (peaks in Hough space)
        # Adjust min_distance and min_angle if needed
        accum, angles, dists = hough_line_peaks(h, theta, d, num_peaks=num_peaks, min_distance=5, min_angle=5)
    except Exception as e:
        # Can fail if no significant peaks are found
        logger.warning(f"Hough peak finding failed (potentially no distinct lines found): {e}")
        return 0.0

    if angles.size == 0:
         logger.debug("No significant peaks found in Hough transform.")
         return 0.0

    # 4. Estimate Angle
    # Calculate the median angle, converting from radians to degrees
    # We expect the dominant angle to be the skew
    median_angle_rad = np.median(angles)
    skew_angle_deg = np.rad2deg(median_angle_rad)

    logger.debug(f"Detected angles (rad): {angles}")
    logger.debug(f"Median angle (rad): {median_angle_rad}, Estimated skew (deg): {skew_angle_deg:.2f}")

    # Optional: Further refinement - check angle distribution, standard deviation etc.

    # Ensure angle is within expected document skew range, otherwise assume 0
    # (This helps filter out cases where vertical lines might dominate)
    if not (angle_range[0] <= skew_angle_deg <= angle_range[1]):
         logger.debug(f"Estimated angle {skew_angle_deg:.2f} is outside range {angle_range}. Assuming no skew.")
         return 0.0

    return skew_angle_deg

# --- Main Preprocessing Function ---
def preprocess_image(img_pil: Image.Image) -> Image.Image:
    """Applies a preprocessing pipeline to a PIL Image object using Scikit-image.

    Pipeline: Deskew -> Grayscale -> Median -> CLAHE -> Sauvola -> [Crop (TODO)]

    Args:
        img_pil: The input PIL Image object.

    Returns:
        A new PIL Image object with preprocessing applied.
    """
    if not isinstance(img_pil, Image.Image):
        msg = "Invalid input type for preprocess_image: Expected PIL Image."
        logger.error(msg)
        raise TypeError(msg)

    logger.info(f"Preprocessing image (mode: {img_pil.mode}, size: {img_pil.size})...")

    # --- Convert PIL Image to NumPy array ---
    try:
        img_array = np.array(img_pil)
        if img_array.ndim == 3 and img_array.shape[2] == 4:
             logger.debug("Detected RGBA image, converting to RGB first.")
             img_array = img_array[:, :, :3]
        img_float = img_as_float(img_array)
        logger.debug(f"Converted PIL image to NumPy array (shape: {img_float.shape}, dtype: {img_float.dtype}).")
    except Exception as e:
        logger.error(f"Error converting PIL image to NumPy array: {e}", exc_info=True)
        raise

    processed_img = img_float

    # --- Step 1: Convert to Grayscale (Needed for Deskewing) ---
    if processed_img.ndim == 3:
        logger.debug("Converting to grayscale for deskewing...")
        try:
            processed_img_gray = rgb2gray(processed_img)
            logger.debug(f"Converted to grayscale (shape: {processed_img_gray.shape}, dtype: {processed_img_gray.dtype}).")
        except Exception as e:
             logger.warning(f"Failed to convert to grayscale: {e}", exc_info=True)
             processed_img_gray = processed_img # Try proceeding if already 1 channel? Risky.
    else:
        processed_img_gray = processed_img # Assume already grayscale if not 3 dims


    # --- Step 2: Deskewing ---
    logger.debug("Attempting deskewing...")
    try:
        # Estimate skew on the grayscale image
        skew_angle = estimate_skew_angle(processed_img_gray)
        # Only rotate if skew is significant (e.g., > 0.1 degrees magnitude)
        if abs(skew_angle) > 0.1:
            logger.info(f"Estimated skew angle: {skew_angle:.2f} degrees. Rotating image...")
            # Rotate the original float image (color or gray)
            # Use white background fill, resize to fit rotated image
            processed_img = rotate(processed_img, skew_angle, resize=True, mode='constant', cval=1.0, order=1) # cval=1 for white bg on float
            logger.debug("Image rotated.")
            # After rotation, if we started with color, we need grayscale again for next steps
            if processed_img.ndim == 3:
                 processed_img_gray = rgb2gray(processed_img)
            else:
                 processed_img_gray = processed_img
        else:
            logger.debug("Skew angle not significant. Skipping rotation.")
            # Ensure processed_img_gray holds the correct grayscale version
            if processed_img.ndim == 3: processed_img_gray = rgb2gray(processed_img)
            else: processed_img_gray = processed_img

    except Exception as e:
        logger.warning(f"Deskewing failed: {e}", exc_info=True)
        # Continue with the potentially skewed grayscale image
        if processed_img.ndim == 3: processed_img_gray = rgb2gray(processed_img)
        else: processed_img_gray = processed_img


    # --- Step 3: Median Filter (Noise Reduction) ---
    # Apply to the (potentially deskewed) grayscale image
    logger.debug("Applying Median Filter...")
    try:
        with np.errstate(invalid='ignore'):
            img_uint8_med = img_as_ubyte(processed_img_gray)
        processed_img_median = median(img_uint8_med, footprint=disk(1))
        processed_img = img_as_float(processed_img_median) # Back to float
        logger.debug("Applied Median Filter.")
    except Exception as e:
        logger.warning(f"Failed to apply Median Filter: {e}", exc_info=True)
        processed_img = processed_img_gray # Fallback to image before filter

    # --- Step 4: CLAHE (Contrast Enhancement) ---
    logger.debug("Applying CLAHE...")
    try:
        processed_img = equalize_adapthist(processed_img, clip_limit=0.01)
        logger.debug("Applied CLAHE.")
    except Exception as e:
        logger.warning(f"Failed to apply CLAHE: {e}", exc_info=True)
        # Continue with image before CLAHE

    # --- Step 5: Binarization (Sauvola) ---
    logger.debug("Applying Sauvola Binarization...")
    try:
        window_size = 15
        k = 0.2
        # Ensure input is float
        if processed_img.dtype != np.float64 and processed_img.dtype != np.float32:
            processed_img_float_bin = img_as_float(processed_img)
        else:
            processed_img_float_bin = processed_img

        thresh_sauvola = threshold_sauvola(processed_img_float_bin, window_size=window_size, k=k)
        binary_sauvola = processed_img_float_bin > thresh_sauvola
        processed_img = img_as_ubyte(binary_sauvola) # Final output is uint8 binary
        logger.debug(f"Applied Sauvola Binarization (window={window_size}, k={k}).")
    except Exception as e:
        logger.warning(f"Failed to apply Sauvola Binarization: {e}", exc_info=True)
        # Fallback if binarization fails
        if processed_img.dtype != np.uint8:
             logger.warning("Binarization failed, attempting fallback uint8 conversion.")
             try:
                 processed_img = img_as_ubyte(processed_img > 0.5) if np.max(processed_img) <= 1.0 else processed_img.astype(np.uint8)
             except Exception as fallback_e:
                  logger.error(f"Fallback uint8 conversion failed: {fallback_e}", exc_info=True)
                  raise Exception("Failed to convert processed image to uint8") from fallback_e

    # --- Step 6: [Placeholder] Cropping ---
    logger.debug("Skipping Cropping (Placeholder).")
    # TODO: Implement cropping

    # --- Convert final NumPy array back to PIL Image ---
    logger.debug(f"Converting final NumPy array (shape: {processed_img.shape}, dtype: {processed_img.dtype}) back to PIL Image...")
    try:
        if processed_img.dtype != np.uint8:
            logger.error(f"Final image array is not uint8 ({processed_img.dtype})!")
            processed_img_final = img_as_ubyte(processed_img)
        else:
            processed_img_final = processed_img
        final_pil_image = Image.fromarray(processed_img_final)
        logger.info(f"Preprocessing complete. Final PIL Image mode: {final_pil_image.mode}")
        return final_pil_image
    except Exception as e:
        logger.error(f"Error converting final NumPy array to PIL Image: {e}", exc_info=True)
        raise

# Example usage block (remains the same)
if __name__ == "__main__":
    # ...(Testing block remains unchanged)...
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(name)s - %(message)s')
    logger.info("--- Running image_processor.py directly for testing ---")
    test_image_dir = "temp_test_loader"
    test_image_path = os.path.join(test_image_dir, "test_loader_image.webp")
    processed_image_path = os.path.join(test_image_dir, "processed_skimage_test_image.png")
    if os.path.exists(test_image_path):
        logger.info(f"Loading test image: {test_image_path}")
        input_image = None; processed_image = None
        try:
            input_image = Image.open(test_image_path); input_image.load()
            logger.info(f"Input image loaded: mode={input_image.mode}, size={input_image.size}")
            processed_image = preprocess_image(input_image)
            logger.info(f"Saving processed image to: {processed_image_path}")
            processed_image.save(processed_image_path, format="PNG")
            logger.info(f"Test processing complete. Check the output image: {processed_image_path}")
        except FileNotFoundError: logger.error(f"Test image not found at {test_image_path}")
        except ImportError: logger.error("scikit-image not installed. Cannot run test.")
        except Exception as e: logger.error(f"An error occurred during testing: {e}", exc_info=True)
        finally:
            if input_image: input_image.close()
            if processed_image: processed_image.close()
            logger.info(f"(Remember to manually clean up '{test_image_dir}' directory if needed)")
    else:
        logger.warning(f"Test image not found at '{test_image_path}'.")
        logger.warning("Please ensure the test image exists (e.g., by running the loader.py test first)")
    logger.info("--- Image Processor Test Complete ---")