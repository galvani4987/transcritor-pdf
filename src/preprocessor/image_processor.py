# -*- coding: utf-8 -*-
"""
Module for preprocessing individual page images before OCR/extraction.

Applies techniques like grayscale conversion, binarization, noise reduction,
contrast adjustment, etc. to improve the quality of the image for text
recognition, especially for handwritten documents.
"""

from PIL import Image, ImageFilter, ImageOps # Import Pillow modules for image operations
import sys # For potential error output
import os # For testing block

def preprocess_image(img: Image.Image) -> Image.Image:
    """
    Applies a series of preprocessing steps to a PIL Image object.

    The specific steps and their parameters might need tuning based on
    the characteristics of the input documents and the OCR engine used.

    Args:
        img: The input PIL Image object (representing a document page),
             loaded by the input_handler.loader module.

    Returns:
        A new PIL Image object with preprocessing applied.
        The returned image should be in a format suitable for the extractor module.
    """
    if not isinstance(img, Image.Image):
        raise TypeError("Input must be a PIL Image object.")

    print(f"Preprocessing image (mode: {img.mode}, size: {img.size})...")

    # --- Step 1: Convert to Grayscale ---
    # Often beneficial for OCR and simplifies subsequent steps.
    processed_img = img.convert('L') # 'L' mode is 8-bit grayscale
    print("  Converted to grayscale.")

    # --- Step 2: Noise Reduction (Example: Median Filter) ---
    # Helps remove salt-and-pepper noise common in scans.
    # Kernel size (e.g., 3) might need adjustment.
    # Note: This step is commented out by default, enable and test if needed.
    # try:
    #     processed_img = processed_img.filter(ImageFilter.MedianFilter(size=3))
    #     print("  Applied Median Filter.")
    # except Exception as e:
    #     print(f"  Warning: Failed to apply Median Filter: {e}", file=sys.stderr)


    # --- Step 3: Contrast Enhancement (Example: Autocontrast) ---
    # Can improve readability if contrast is poor.
    # Note: This step is commented out by default, enable and test if needed.
    # try:
    #     processed_img = ImageOps.autocontrast(processed_img)
    #     print("  Applied Autocontrast.")
    # except Exception as e:
    #     print(f"  Warning: Failed to apply Autocontrast: {e}", file=sys.stderr)


    # --- Step 4: Binarization (Example: Simple Thresholding - Often less effective than adaptive) ---
    # Converts the image to black and white. Crucial for some OCR engines.
    # Finding the right threshold is key and often document-dependent.
    # Adaptive thresholding methods (e.g., using OpenCV) are generally superior
    # but add complexity and dependencies. Let's keep it simple for now.
    # Note: This step is commented out by default, enable and tune if needed.
    # try:
    #     threshold = 180 # Example threshold value (0-255), NEEDS TUNING!
    #     # Use point operation for thresholding, '1' mode is bilevel (B&W)
    #     # processed_img_bw = processed_img.point(lambda p: 0 if p < threshold else 255, '1')
    #     # Convert back to 'L' as some libraries might prefer grayscale over bilevel
    #     # processed_img = processed_img_bw.convert('L')
    #     # print(f"  Applied Binarization (Threshold: {threshold}).")
    # except Exception as e:
    #     print(f"  Warning: Failed to apply Binarization: {e}", file=sys.stderr)


    # --- Step 5: Sharpening (Example: Unsharp Mask) ---
    # Can sometimes enhance edges of text, but use with caution as it can amplify noise.
    # Note: This step is commented out by default, enable and test if needed.
    # try:
    #     processed_img = processed_img.filter(ImageFilter.UnsharpMask(radius=1, percent=150, threshold=3))
    #     print("  Applied Unsharp Mask.")
    # except Exception as e:
    #     print(f"  Warning: Failed to apply Unsharp Mask: {e}", file=sys.stderr)


    # --- End of Processing Steps ---
    print(f"Preprocessing complete. Output image mode: {processed_img.mode}, size: {processed_img.size}")

    # Return the final processed image (should be a PIL Image object)
    return processed_img

# Example usage block (for testing when script is run directly)
if __name__ == "__main__":
    print("\n--- Running image_processor.py directly for testing ---")
    # Assumes the dummy image from loader.py test might exist
    test_image_dir = "temp_test_loader"
    test_image_path = os.path.join(test_image_dir, "test_loader_image.webp") # Path to the source test image

    processed_image_path = os.path.join(test_image_dir, "processed_test_image.png") # Where to save output

    if os.path.exists(test_image_path):
        print(f"\nLoading test image: {test_image_path}")
        input_image = None
        processed_image = None
        try:
            input_image = Image.open(test_image_path)
            input_image.load()
            print(f"Input image loaded: mode={input_image.mode}, size={input_image.size}")

            # Apply preprocessing
            processed_image = preprocess_image(input_image)

            # Save the processed image for visual inspection
            print(f"\nSaving processed image to: {processed_image_path}")
            processed_image.save(processed_image_path, format="PNG") # Save as PNG for easy viewing

            print("\nTest processing complete. Check the output image:", processed_image_path)

        except FileNotFoundError:
             print(f"Error: Test image not found at {test_image_path}")
        except Exception as e:
             print(f"An error occurred during testing: {e}")
        finally:
            # Close images if they were opened
            if input_image:
                input_image.close()
            if processed_image:
                processed_image.close()
            # Note: We leave the dummy input and processed output files for inspection.
            # Manual cleanup might be needed for the test directory.
            print(f"\n(Remember to manually clean up '{test_image_dir}' directory if needed)")

    else:
        print(f"\nTest image not found at '{test_image_path}'.")
        print(f"Please ensure the test image exists (e.g., by running the loader.py test first)")
        print(f"or update the 'test_image_path' variable in this script.")

    print("\n--- Image Processor Test Complete ---")