# -*- coding: utf-8 -*-
"""
Module responsible for splitting PDF files into individual page images.

Handles potentially large PDFs by saving extracted pages as temporary
image files on disk using WebP lossless format. Includes logging.
"""

import pypdfium2 as pdfium
import os
import sys
import logging # Import logging
from typing import Generator

# Get a logger instance for this module
logger = logging.getLogger(__name__)

# Define potential output directory for temporary page images
TEMP_PAGE_DIR = "temp_pdf_pages" # Store temporary page images here

# Define type hint for the yielded item (will be file path)
PageOutputType = str

def split_pdf_to_pages(pdf_path: str) -> Generator[PageOutputType, None, None]:
    """
    Splits a large PDF file into individual page images saved temporarily on disk
    in WebP lossless format.

    Args:
        pdf_path: The path to the input PDF file.

    Yields:
        Paths to temporary image files (WebP format) representing each page.

    Raises:
        FileNotFoundError: If the pdf_path does not exist.
        pdfium.PdfiumError: If there's an error processing the PDF with pypdfium2.
        OSError: If the temporary directory cannot be created.
        Exception: For other unexpected errors during processing.
    """
    if not os.path.isfile(pdf_path):
        error_msg = f"Input PDF not found at: {pdf_path}"
        logger.error(error_msg)
        raise FileNotFoundError(error_msg)

    # Ensure temporary directory exists
    try:
        os.makedirs(TEMP_PAGE_DIR, exist_ok=True)
        logger.info(f"Ensured temporary directory exists: '{TEMP_PAGE_DIR}'")
    except OSError as e:
        logger.error(f"Error creating temporary directory '{TEMP_PAGE_DIR}': {e}", exc_info=True)
        raise # Re-raise the error as we cannot proceed

    logger.info(f"Starting PDF splitting for: {pdf_path} (Saving pages as WebP Lossless)")
    pdf = None
    try:
        pdf = pdfium.PdfDocument(pdf_path)
        n_pages = len(pdf)
        logger.info(f"PDF contains {n_pages} pages.")

        pdf_basename = os.path.splitext(os.path.basename(pdf_path))[0]
        safe_basename = "".join(c if c.isalnum() or c in ('_', '-') else '_' for c in pdf_basename)
        temp_file_prefix = f"{safe_basename}_page_"

        for i in range(n_pages):
            page_number = i + 1
            page = None
            bitmap = None
            temp_image_path = None

            try:
                temp_image_filename = f"{temp_file_prefix}{page_number:04d}.webp"
                temp_image_path = os.path.join(TEMP_PAGE_DIR, temp_image_filename)

                page = pdf.get_page(i)
                # Consider logging DPI/scale if configurable later
                bitmap = page.render(scale=2) # Render at 144 DPI (example)
                bitmap.save(temp_image_path, format="webp", lossless=True)

                logger.debug(f"Successfully saved page {page_number} to: {temp_image_path} (WebP Lossless)") # Use DEBUG for per-page success
                yield temp_image_path

            except Exception as page_error:
                logger.error(f"Error processing page {page_number} of '{pdf_path}': {page_error}", exc_info=True)
                # Continue to next page if one fails
            finally:
                if bitmap: bitmap.close()
                if page: page.close()

        logger.info(f"Finished processing all pages for '{pdf_path}'.")

    except pdfium.PdfiumError as e:
        logger.error(f"Error processing PDF '{pdf_path}' with pypdfium2: {e}", exc_info=True)
        raise
    except Exception as e:
        logger.error(f"An unexpected error occurred during PDF splitting for '{pdf_path}': {e}", exc_info=True)
        raise
    finally:
        if pdf:
            pdf.close()
            logger.info(f"Closed PDF document: {pdf_path}")

# Example usage block (for testing when script is run directly)
if __name__ == "__main__":
    # Configure logging specifically for the test run if needed
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(name)s - %(message)s')
    logger.info("--- Running pdf_splitter.py directly for testing ---")

    test_pdf_path = "test_document.pdf" # <<< CHANGE THIS PATH IF NEEDED

    if os.path.exists(test_pdf_path):
        logger.info(f"Testing PDF splitting for '{test_pdf_path}' (saving temporary WebP lossless images):")
        generated_paths = []
        try:
            generated_paths = list(split_pdf_to_pages(test_pdf_path))
            page_count = len(generated_paths)
            logger.info(f"Successfully yielded {page_count} temporary page image paths.")
            if generated_paths:
                logger.info(f"Example path: {generated_paths[0]}")
                logger.info(f"(Files are located in '{TEMP_PAGE_DIR}')")

        except FileNotFoundError as e:
            logger.error(f"Error: {e}")
        except pdfium.PdfiumError as e:
             logger.error(f"Error during pypdfium2 processing: {e}")
        except Exception as e:
            logger.error(f"An unexpected error occurred during the test: {e}", exc_info=True)
        finally:
            # Clean up generated temporary files after testing
            if generated_paths:
                logger.info("Cleaning up temporary files...")
                files_removed_count = 0
                for p in generated_paths:
                    if os.path.exists(p):
                        try:
                            os.remove(p)
                            files_removed_count += 1
                        except OSError as e:
                            logger.warning(f"Error removing file {p}: {e}")
                logger.info(f"Removed {files_removed_count} temporary image files.")

            try:
                if os.path.exists(TEMP_PAGE_DIR) and not os.listdir(TEMP_PAGE_DIR):
                    os.rmdir(TEMP_PAGE_DIR)
                    logger.info(f"Removed empty temporary directory: '{TEMP_PAGE_DIR}'")
            except OSError as e:
                logger.warning(f"Could not remove directory '{TEMP_PAGE_DIR}': {e}")

    else:
        logger.warning(f"Test PDF file not found at '{test_pdf_path}'.")
        logger.warning("To run this test block, place a valid PDF file named")
        logger.warning(f"'{os.path.basename(test_pdf_path)}' in the project's root directory, OR")
        logger.warning(f"update the 'test_pdf_path' variable in this script.")

    logger.info("--- PDF Splitter Test Complete ---")