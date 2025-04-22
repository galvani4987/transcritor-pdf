# -*- coding: utf-8 -*-
"""
Module for preprocessing individual page images before OCR/extraction.

Applies techniques based on research findings (Grayscale, Median Filter,
CLAHE, Sauvola Binarization) primarily using Scikit-image to improve
readability of handwritten medical documents.
"""

from PIL import Image
import numpy as np # Scikit-image works with NumPy arrays
import sys
import os

# Import necessary functions from Scikit-image
try:
    from skimage import io as skimage_io
    from skimage.color import rgb2gray # Handles conversion correctly
    from skimage.filters import median, threshold_sauvola
    from skimage.morphology import disk
    from skimage.exposure import equalize_adapthist # CLAHE implementation
    from skimage.util import img_as_ubyte, img_as_float # For type conversions
    # For Deskewing (if implemented later)
    # from skimage.transform import rotate, hough_line, hough_line_peaks
    # from skimage.feature import canny
except ImportError:
    print("Error: scikit-image library not found. Please install it using:", file=sys.stderr)
    print("pip install scikit-image", file=sys.stderr)
    sys.exit(1)

def preprocess_image(img_pil: Image.Image) -> Image.Image:
    """
    Applies a preprocessing pipeline to a PIL Image object using Scikit-image.

    Pipeline based on research:
    1. [Optional/TODO] Deskewing
    2. Convert to Grayscale
    3. Median Filter (Noise Reduction)
    4. CLAHE (Contrast Enhancement)
    5. Sauvola Binarization
    6. [Optional/TODO] Cropping

    Args:
        img_pil: The input PIL Image object (representing a document page).

    Returns:
        A new PIL Image object (likely grayscale or binary) with preprocessing applied.
    """
    if not isinstance(img_pil, Image.Image):
        raise TypeError("Input must be a PIL Image object.")

    print(f"Preprocessing image (mode: {img_pil.mode}, size: {img_pil.size})...")

    # --- Convert PIL Image to NumPy array for Scikit-image ---
    # Use img_as_float for many skimage functions which expect float values in [0, 1]
    try:
        img_array = np.array(img_pil)
        # Handle different input modes (e.g., RGBA, RGB, L)
        if img_array.ndim == 3 and img_array.shape[2] == 4: # RGBA
             print("  Detected RGBA image, converting to RGB first.")
             img_array = img_array[:, :, :3] # Drop alpha channel

        # Convert to float for processing
        img_float = img_as_float(img_array)
        print(f"  Converted PIL image to NumPy array (shape: {img_float.shape}, dtype: {img_float.dtype}).")
    except Exception as e:
        print(f"Error converting PIL image to NumPy array: {e}", file=sys.stderr)
        raise

    processed_img = img_float # Start with the float image

    # --- Step 1: [Placeholder] Deskewing ---
    # TODO: Implement deskewing logic here if needed.
    # This often involves detecting the skew angle and rotating.
    # angle = estimate_skew_angle(processed_img) # Hypothetical function
    # processed_img = rotate(processed_img, angle, resize=True, mode='edge') * 255
    print("  Skipping Deskewing (Placeholder).")


    # --- Step 2: Convert to Grayscale ---
    # Ensure grayscale conversion happens correctly if not already grayscale
    if processed_img.ndim == 3: # Check if it has color channels
        print("  Converting to grayscale...")
        # rgb2gray handles luminance correctly and outputs float in [0, 1]
        processed_img = rgb2gray(processed_img)
        print(f"  Converted to grayscale (shape: {processed_img.shape}, dtype: {processed_img.dtype}).")
    elif processed_img.dtype != np.float64 and processed_img.dtype != np.float32:
        # If already single channel but not float, convert
        processed_img = img_as_float(processed_img)


    # --- Step 3: Median Filter (Noise Reduction) ---
    print("  Applying Median Filter...")
    try:
        # Use a small disk footprint (3x3 equivalent) as starting point
        # footprint = disk(1) # Removed in newer skimage? Use selem=disk(1)
        # median function expects uint8 or uint16, convert back temporarily
        img_uint8 = img_as_ubyte(processed_img)
        processed_img_median = median(img_uint8, footprint=disk(1)) # Use footprint=disk(1) or selem=disk(1) depending on version
        processed_img = img_as_float(processed_img_median) # Convert back to float
        print("  Applied Median Filter.")
    except Exception as e:
        print(f"  Warning: Failed to apply Median Filter: {e}", file=sys.stderr)
        # Continue with the image before median filter if it fails


    # --- Step 4: CLAHE (Contrast Enhancement) ---
    print("  Applying CLAHE...")
    try:
        # clip_limit is a key parameter to tune. Lower values reduce noise amplification.
        # kernel_size (implicitly defined by grid size) also affects locality.
        # equalize_adapthist works on float images directly.
        processed_img = equalize_adapthist(processed_img, clip_limit=0.01) # Start with low clip limit
        print("  Applied CLAHE.")
    except Exception as e:
        print(f"  Warning: Failed to apply CLAHE: {e}", file=sys.stderr)
        # Continue with the image before CLAHE if it fails


    # --- Step 5: Binarization (Sauvola) ---
    print("  Applying Sauvola Binarization...")
    try:
        # Sauvola works well on grayscale images. Parameters need tuning.
        # window_size should be odd and appropriate for character size.
        # k is a threshold parameter.
        window_size = 15 # Example starting value
        k = 0.2 # Example starting value
        thresh_sauvola = threshold_sauvola(processed_img, window_size=window_size, k=k)
        # Apply threshold: pixels below threshold become 0 (black), above become 1 (white)
        # Note: Sauvola output is boolean by default, convert for image display/saving
        binary_sauvola = processed_img > thresh_sauvola
        # Convert boolean array to uint8 (0 or 255) for PIL compatibility
        processed_img = img_as_ubyte(binary_sauvola)
        print(f"  Applied Sauvola Binarization (window={window_size}, k={k}). Output is now uint8 binary.")
    except Exception as e:
        print(f"  Warning: Failed to apply Sauvola Binarization: {e}", file=sys.stderr)
        # If binarization fails, maybe return the grayscale image before it?
        # For now, continue with whatever processed_img holds (might be grayscale float)
        # Convert to uint8 if not already binary, for consistency
        if processed_img.dtype != np.uint8:
             processed_img = img_as_ubyte(processed_img > 0.5) # Fallback simple threshold if needed


    # --- Step 6: [Placeholder] Cropping ---
    # TODO: Implement logic to find content bounds and crop if needed.
    print("  Skipping Cropping (Placeholder).")


    # --- Convert final NumPy array back to PIL Image ---
    print(f"Converting final NumPy array (shape: {processed_img.shape}, dtype: {processed_img.dtype}) back to PIL Image...")
    try:
        # Ensure the array is in a format PIL understands (like uint8)
        if processed_img.dtype != np.uint8:
            print(f"  Warning: Final image array is not uint8 ({processed_img.dtype}), attempting conversion.", file=sys.stderr)
            # Be careful with float conversion, might need scaling if not in [0, 1]
            if np.max(processed_img) <= 1.0 and np.min(processed_img) >= 0.0:
                 processed_img_final = img_as_ubyte(processed_img)
            else:
                 # Attempt simple cast if values seem out of float range (less safe)
                 processed_img_final = processed_img.astype(np.uint8)
        else:
            processed_img_final = processed_img

        final_pil_image = Image.fromarray(processed_img_final)
        # If the output is binary (0, 255), the mode might be 'L'.
        # If it failed and is still grayscale float converted to uint8, it's 'L'.
        print(f"Preprocessing complete. Final PIL Image mode: {final_pil_image.mode}")
        return final_pil_image
    except Exception as e:
        print(f"Error converting final NumPy array to PIL Image: {e}", file=sys.stderr)
        raise

# Example usage block (for testing when script is run directly)
if __name__ == "__main__":
    print("\n--- Running image_processor.py directly for testing ---")
    # Assumes the dummy image from loader.py test might exist
    test_image_dir = "temp_test_loader"
    # Use the original dummy image for testing the full pipeline
    test_image_path = os.path.join(test_image_dir, "test_loader_image.webp")

    processed_image_path = os.path.join(test_image_dir, "processed_skimage_test_image.png") # Save output here

    if os.path.exists(test_image_path):
        print(f"\nLoading test image: {test_image_path}")
        input_image = None
        processed_image = None
        try:
            input_image = Image.open(test_image_path)
            input_image.load()
            print(f"Input image loaded: mode={input_image.mode}, size={input_image.size}")

            # Apply preprocessing using the updated function
            processed_image = preprocess_image(input_image)

            # Save the processed image for visual inspection
            print(f"\nSaving processed image to: {processed_image_path}")
            processed_image.save(processed_image_path, format="PNG")

            print("\nTest processing complete. Check the output image:", processed_image_path)

        except FileNotFoundError:
             print(f"Error: Test image not found at {test_image_path}")
        except ImportError:
             print("Error: scikit-image not installed. Cannot run test.") # Caught by import block too
        except Exception as e:
             print(f"An error occurred during testing: {e}")
        finally:
            # Close images if they were opened
            if input_image:
                input_image.close()
            if processed_image:
                processed_image.close()
            print(f"\n(Remember to manually clean up '{test_image_dir}' directory if needed)")

    else:
        print(f"\nTest image not found at '{test_image_path}'.")
        print(f"Please ensure the test image exists (e.g., by running the loader.py test first)")
        print(f"or update the 'test_image_path' variable in this script.")

    print("\n--- Image Processor Test Complete ---")