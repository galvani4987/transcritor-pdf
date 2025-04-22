# -*- coding: utf-8 -*-
"""
Module responsible for splitting PDF files into individual page images.

Handles potentially large PDFs by saving extracted pages as temporary
image files on disk using WebP lossless format to conserve disk space
while maintaining quality for OCR.
"""

import pypdfium2 as pdfium
import os
import sys # For error output
from typing import Generator
# PIL is implicitly used by bitmap.save() for WEBP

# Define potential output directory for temporary page images
# Consider making this configurable later via config file or CLI arg
TEMP_PAGE_DIR = "temp_pdf_pages" # Store temporary page images here

# Define type hint for the yielded item (will be file path)
PageOutputType = str

def split_pdf_to_pages(pdf_path: str) -> Generator[PageOutputType, None, None]:
    """
    Splits a large PDF file into individual page images saved temporarily on disk
    in WebP lossless format.

    Args:
        pdf_path: The absolute or relative path to the input PDF file.

    Yields:
        Paths to temporary image files (WebP format) representing each page.
        The files are saved in the TEMP_PAGE_DIR directory.

    Raises:
        FileNotFoundError: If the pdf_path does not exist.
        pdfium.PdfiumError: If there's an error processing the PDF with pypdfium2.
        OSError: If the temporary directory cannot be created.
        Exception: For other unexpected errors during processing.
    """
    if not os.path.isfile(pdf_path):
        raise FileNotFoundError(f"Input PDF not found at: {pdf_path}")

    # Ensure temporary directory exists
    try:
        # exist_ok=True prevents error if directory already exists
        os.makedirs(TEMP_PAGE_DIR, exist_ok=True)
        print(f"Ensured temporary directory exists: '{TEMP_PAGE_DIR}'")
    except OSError as e:
        print(f"Error creating temporary directory '{TEMP_PAGE_DIR}': {e}", file=sys.stderr)
        raise # Re-raise the error as we cannot proceed without the temp dir

    print(f"Starting PDF splitting for: {pdf_path} (Saving pages as WebP Lossless)")
    pdf = None # Initialize pdf variable to ensure it's available in finally block
    try:
        pdf = pdfium.PdfDocument(pdf_path) # Load PDF document
        n_pages = len(pdf)
        print(f"PDF contains {n_pages} pages.")

        # Generate a unique prefix for this PDF's temp files
        pdf_basename = os.path.splitext(os.path.basename(pdf_path))[0]
        safe_basename = "".join(c if c.isalnum() or c in ('_', '-') else '_' for c in pdf_basename)
        temp_file_prefix = f"{safe_basename}_page_"

        for i in range(n_pages):
            page_number = i + 1
            page = None # Initialize page variable for this iteration
            bitmap = None # Initialize bitmap variable for this iteration
            temp_image_path = None # Initialize path variable

            try:
                # Construct the temporary file path for this page with .webp extension
                temp_image_filename = f"{temp_file_prefix}{page_number:04d}.webp" # Use .webp extension
                temp_image_path = os.path.join(TEMP_PAGE_DIR, temp_image_filename)

                # Get page object
                page = pdf.get_page(i)

                # Render page to an image (bitmap)
                # Adjust scale as needed for OCR quality vs performance trade-off
                bitmap = page.render(scale=2) # Render at 144 DPI (example)

                # Save the bitmap directly to a WebP file (lossless)
                # Ensure lossless=True for optimal OCR quality
                bitmap.save(temp_image_path, format="webp", lossless=True) # Save as WEBP lossless

                print(f"  Successfully saved page {page_number} to: {temp_image_path} (WebP Lossless)")
                yield temp_image_path # Yield path to the saved image file

            except Exception as page_error:
                # Log error for the specific page and continue if possible
                print(f"  Error processing page {page_number} of '{pdf_path}': {page_error}", file=sys.stderr)
            finally:
                # Ensure resources for the current page are released
                if bitmap:
                    bitmap.close()
                if page:
                    page.close()

        print(f"Finished processing all pages for '{pdf_path}'.")

    except pdfium.PdfiumError as e:
        # Handle errors during PDF loading or general processing
        print(f"Error processing PDF '{pdf_path}' with pypdfium2: {e}", file=sys.stderr)
        raise
    except Exception as e:
        # Handle any other unexpected errors
        print(f"An unexpected error occurred during PDF splitting for '{pdf_path}': {e}", file=sys.stderr)
        raise
    finally:
        # Ensure the main PDF document is closed if it was opened
        if pdf:
            pdf.close()
            print(f"Closed PDF document: {pdf_path}")

# Example usage block (for testing when script is run directly)
if __name__ == "__main__":
    print("\n--- Running pdf_splitter.py directly for testing ---")
    # IMPORTANT: Replace with a real path to a test PDF file in your project root
    test_pdf_path = "test_document.pdf" # <<< CHANGE THIS PATH IF NEEDED

    if os.path.exists(test_pdf_path):
        print(f"\nTesting PDF splitting for '{test_pdf_path}' (saving temporary WebP lossless images):")
        generated_paths = []
        try:
            # Use list() to consume the generator and execute the splitting process
            generated_paths = list(split_pdf_to_pages(test_pdf_path))
            page_count = len(generated_paths)
            print(f"\nSuccessfully yielded {page_count} temporary page image paths (WebP Lossless).")
            if generated_paths:
                print(f"Example path: {generated_paths[0]}")
                print(f"(Files are located in '{TEMP_PAGE_DIR}')")

        except FileNotFoundError as e:
            print(f"\nError: {e}")
        except pdfium.PdfiumError as e:
             print(f"\nError during pypdfium2 processing: {e}")
        except Exception as e:
            print(f"\nAn unexpected error occurred during the test: {e}")
        finally:
            # Clean up generated temporary files after testing
            if generated_paths:
                print("\nCleaning up temporary files...")
                files_removed_count = 0
                for p in generated_paths:
                    if os.path.exists(p):
                        try:
                            os.remove(p)
                            files_removed_count += 1
                        except OSError as e:
                            print(f"  Error removing file {p}: {e}", file=sys.stderr)
                print(f"Removed {files_removed_count} temporary image files.")

            # Attempt to remove the temporary directory if it exists and is empty
            try:
                if os.path.exists(TEMP_PAGE_DIR) and not os.listdir(TEMP_PAGE_DIR):
                    os.rmdir(TEMP_PAGE_DIR)
                    print(f"Removed empty temporary directory: '{TEMP_PAGE_DIR}'")
            except OSError as e:
                print(f"  Note: Could not remove directory '{TEMP_PAGE_DIR}': {e}", file=sys.stderr)

    else:
        # Instructions if the test file doesn't exist
        print(f"\nTest PDF file not found at '{test_pdf_path}'.")
        print("To run this test block:")
        print(f" 1. Place a valid PDF file named '{os.path.basename(test_pdf_path)}' in the project's root directory, OR")
        print(f" 2. Update the 'test_pdf_path' variable inside the 'if __name__ == \"__main__\":' block in this script.")

    print("\n--- PDF Splitter Test Complete ---")