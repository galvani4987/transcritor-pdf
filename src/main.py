# -*- coding: utf-8 -*-
"""
Main entry point for the Transcritor PDF CLI application.

Orchestrates the workflow: split PDF -> load page -> preprocess page ->
extract info -> format output -> vectorize & store.
"""
import argparse
import sys
import os

# Import functions from our modules
from .input_handler.pdf_splitter import split_pdf_to_pages, TEMP_PAGE_DIR
from .input_handler.loader import load_page_image
# Import the preprocessing function
from .preprocessor.image_processor import preprocess_image
# from .extractor import llm_client, text_extractor, info_parser # Placeholder
# from .output_handler import formatter # Placeholder
# from .vectorizer import embedding_generator, vector_store_handler # Placeholder

# --- Utility function for cleaning up temporary files ---
def cleanup_temp_files(temp_files: list[str]):
    """Removes the temporary files created during processing."""
    print("\nCleaning up temporary page files...")
    files_removed_count = 0
    for file_path in temp_files:
        if file_path and isinstance(file_path, str) and os.path.exists(file_path):
            try:
                os.remove(file_path)
                files_removed_count += 1
            except OSError as e:
                print(f"  Warning: Could not remove temp file {file_path}: {e}", file=sys.stderr)
        elif file_path:
             print(f"  Warning: Temp file path '{file_path}' not found for cleanup.", file=sys.stderr)

    print(f"Removed {files_removed_count} temporary files.")

    try:
        if os.path.exists(TEMP_PAGE_DIR) and not os.listdir(TEMP_PAGE_DIR):
            os.rmdir(TEMP_PAGE_DIR)
            print(f"Removed empty temporary directory: {TEMP_PAGE_DIR}")
    except OSError as e:
        print(f"  Warning: Could not remove temp directory {TEMP_PAGE_DIR}: {e}", file=sys.stderr)


# --- Main Pipeline Function ---
def run_transcription_pipeline(pdf_file_path: str):
    """
    Executes the complete processing pipeline for a given PDF file.

    Args:
        pdf_file_path: The path to the input PDF file.
    """
    print(f"Starting transcription pipeline for: {pdf_file_path}")
    temp_page_paths = []
    all_extracted_data = []

    try:
        print("\n--- Step 1: Splitting PDF into Pages ---")
        page_path_generator = split_pdf_to_pages(pdf_file_path)

        page_number = 0
        for page_path in page_path_generator:
            page_number += 1
            temp_page_paths.append(page_path)
            print(f"\n--- Processing Page {page_number} (File: {page_path}) ---")
            page_image = None
            processed_page_image = None # Variable for the preprocessed image

            try:
                print(f"--- Step 2: Loading Page Image ---")
                page_image = load_page_image(page_path)

                if page_image:
                    # --- Step 3: Preprocess Page Image ---
                    print(f"--- Step 3: Preprocessing Page Image ---")
                    # Call the preprocessing function from image_processor module
                    processed_page_image = preprocess_image(page_image)

                    # --- Step 4: Extract Information from Page (Placeholder) ---
                    print(f"--- Step 4: Extracting Information ---")
                    # Pass the *processed* image to the extractor (when implemented)
                    # extracted_info = text_extractor.extract_text_from_image(processed_page_image) # Example call
                    # parsed_info = info_parser.parse_text(extracted_info_text) # Example call
                    print("  -> (Placeholder) Extraction logic using processed image here.")
                    extracted_info = {
                        "page_number": page_number,
                        "source_file": pdf_file_path,
                        "temp_image_path": page_path,
                        # Indicate that preprocessing was applied (useful for debugging)
                        "preprocessing_applied": True,
                        "extracted_text": f"Placeholder text from PREPROCESSED page {page_number}.",
                    }
                    all_extracted_data.append(extracted_info)

            except FileNotFoundError as e:
                 print(f"  Error: Could not load page image, file not found: {e}. Skipping page {page_number}.", file=sys.stderr)
            except Exception as page_processing_error:
                print(f"  Error processing page {page_number} ({page_path}): {page_processing_error}", file=sys.stderr)
                print(f"  Skipping further processing for page {page_number}.")
            finally:
                # Close the original PIL image object if it was loaded
                if page_image:
                    try:
                        page_image.close()
                    except Exception as close_error:
                        print(f"  Warning: Error closing original image object for page {page_number}: {close_error}", file=sys.stderr)
                # Close the processed PIL image object if it was created
                if processed_page_image:
                     try:
                        processed_page_image.close()
                     except Exception as close_error:
                        print(f"  Warning: Error closing processed image object for page {page_number}: {close_error}", file=sys.stderr)


        if not all_extracted_data:
             print("\nWarning: No data was successfully extracted from any page.", file=sys.stderr)

        print("\n--- Step 5: Formatting Output ---")
        # formatted_output = formatter.format_output(all_extracted_data, pdf_file_path) # TODO
        print("  -> (Placeholder) Formatting logic here.")
        formatted_output = all_extracted_data
        print("  Formatted Output (Placeholder - List of page data):")
        for page_data in formatted_output:
             print(f"    Page {page_data.get('page_number', '?')}: {page_data.get('extracted_text', 'N/A')[:80]}...")

        print("\n--- Step 6: Vectorizing and Storing ---")
        # vectorize_and_store(formatted_output) # TODO
        print("  -> (Placeholder) Vectorization logic here.")

        print("\nPipeline finished successfully.")

    except FileNotFoundError as e:
         print(f"\nPipeline Error: Input file validation failed. {e}", file=sys.stderr)
         sys.exit(1)
    except Exception as pipeline_error:
        print(f"\nPipeline Error: An unexpected error occurred: {pipeline_error}", file=sys.stderr)
        cleanup_temp_files(temp_page_paths)
        sys.exit(1)
    else:
         cleanup_temp_files(temp_page_paths)


# --- CLI Argument Parsing and Execution ---
def main_cli():
    """
    Sets up and runs the CLI argument parser, then starts the pipeline.
    """
    print("--- Transcritor PDF ---")
    parser = argparse.ArgumentParser(
        description="Process a PDF file of handwritten medical documents, extract information, and optionally vectorize."
    )
    parser.add_argument(
        "pdf_file_path",
        type=str,
        help="Path to the PDF file to be processed."
    )
    args = parser.parse_args()
    run_transcription_pipeline(args.pdf_file_path)


if __name__ == "__main__":
    main_cli()