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
# Note the relative import using '.' for modules within the same package (src)
from .input_handler.pdf_splitter import split_pdf_to_pages, TEMP_PAGE_DIR
from .input_handler.loader import load_page_image
# from .preprocessor import image_processor, layout_analyzer # Placeholder for future imports
# from .extractor import llm_client, text_extractor, info_parser # Placeholder
# from .output_handler import formatter # Placeholder
# from .vectorizer import embedding_generator, vector_store_handler # Placeholder

# --- Utility function for cleaning up temporary files ---
def cleanup_temp_files(temp_files: list[str]):
    """Removes the temporary files created during processing."""
    print("\nCleaning up temporary page files...")
    files_removed_count = 0
    for file_path in temp_files:
        # Check if the path is valid and the file exists before trying to remove
        if file_path and isinstance(file_path, str) and os.path.exists(file_path):
            try:
                os.remove(file_path)
                files_removed_count += 1
            except OSError as e:
                # Log warning but continue cleanup
                print(f"  Warning: Could not remove temp file {file_path}: {e}", file=sys.stderr)
        elif file_path:
             print(f"  Warning: Temp file path '{file_path}' not found for cleanup.", file=sys.stderr)

    print(f"Removed {files_removed_count} temporary files.")

    # Optionally remove the temp directory if it's empty
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
    temp_page_paths = [] # Keep track of created temp file paths for cleanup
    all_extracted_data = [] # To store results from all pages

    try:
        # --- Step 1: Split PDF into Page Image Files ---
        print("\n--- Step 1: Splitting PDF into Pages ---")
        # The splitter yields paths to temporary .webp files
        page_path_generator = split_pdf_to_pages(pdf_file_path)

        page_number = 0
        # Iterate through the paths yielded by the splitter
        for page_path in page_path_generator:
            page_number += 1
            temp_page_paths.append(page_path) # Store path for cleanup
            print(f"\n--- Processing Page {page_number} (File: {page_path}) ---")
            page_image = None # Ensure variable scope for finally block

            try:
                # --- Step 2: Load the Page Image ---
                print(f"--- Step 2: Loading Page Image ---")
                # Load the image from the temporary file path
                page_image = load_page_image(page_path)

                # If image loaded successfully, proceed with placeholders
                if page_image:
                    # --- Step 3: Preprocess Page Image (Placeholder) ---
                    print(f"--- Step 3: Preprocessing Page Image ---")
                    # processed_page = preprocess_page(page_image) # TODO: Implement in preprocessor module
                    print("  -> (Placeholder) Preprocessing logic here.")
                    processed_page = page_image # Pass image through for now

                    # --- Step 4: Extract Information from Page (Placeholder) ---
                    print(f"--- Step 4: Extracting Information ---")
                    # extracted_info = extract_page_info(processed_page) # TODO: Implement in extractor module
                    print("  -> (Placeholder) Extraction logic here.")
                    # Dummy data for now, including page number for context
                    extracted_info = {
                        "page_number": page_number,
                        "source_file": pdf_file_path,
                        "temp_image_path": page_path, # Keep track of source image
                        "extracted_text": f"Placeholder text extracted from page {page_number}.",
                        # Add other extracted fields later (name, date, etc.)
                    }
                    all_extracted_data.append(extracted_info)

            except FileNotFoundError as e:
                 # Error from load_page_image if file disappears between split and load
                 print(f"  Error: Could not load page image, file not found: {e}. Skipping page {page_number}.", file=sys.stderr)
            except Exception as page_processing_error:
                # Catch errors during loading or downstream processing of a single page
                print(f"  Error processing page {page_number} ({page_path}): {page_processing_error}", file=sys.stderr)
                print(f"  Skipping further processing for page {page_number}.")
            finally:
                # Close the PIL image object if it was loaded to free resources
                if page_image:
                    try:
                        page_image.close()
                    except Exception as close_error:
                        print(f"  Warning: Error closing image object for page {page_number}: {close_error}", file=sys.stderr)

        # --- Post-Loop Processing Steps (Placeholders) ---
        if not all_extracted_data:
             print("\nWarning: No data was successfully extracted from any page.", file=sys.stderr)
             # Depending on requirements, might want to exit differently here

        # --- Step 5: Format Overall Output (Placeholder) ---
        print("\n--- Step 5: Formatting Output ---")
        # formatted_output = format_output(all_extracted_data, pdf_file_path) # TODO: Implement in output_handler
        print("  -> (Placeholder) Formatting logic here.")
        formatted_output = all_extracted_data # Use the list of dicts for now
        # Basic print of extracted data (for debugging)
        print("  Formatted Output (Placeholder - List of page data):")
        for page_data in formatted_output:
             print(f"    Page {page_data.get('page_number', '?')}: {page_data.get('extracted_text', 'N/A')[:80]}...") # Print snippet

        # --- Step 6: Vectorize and Store (Placeholder) ---
        print("\n--- Step 6: Vectorizing and Storing ---")
        # vectorize_and_store(formatted_output) # TODO: Implement in vectorizer module
        print("  -> (Placeholder) Vectorization logic here.")

        print("\nPipeline finished successfully.")

    except FileNotFoundError as e:
         # Error likely occurred in split_pdf_to_pages before the loop started
         print(f"\nPipeline Error: Input file validation failed. {e}", file=sys.stderr)
         # No temp files created yet, so no cleanup needed here
         sys.exit(1) # Exit with error
    except Exception as pipeline_error:
        # Catch errors from pdf_splitter itself or other top-level issues
        print(f"\nPipeline Error: An unexpected error occurred: {pipeline_error}", file=sys.stderr)
        # Attempt cleanup even if pipeline failed mid-way
        cleanup_temp_files(temp_page_paths)
        sys.exit(1) # Exit with error code after cleanup attempt
    else:
         # Pipeline completed without raising top-level exceptions, perform cleanup
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
        "pdf_file_path", # Argument name matches variable used
        type=str,
        help="Path to the PDF file to be processed."
    )
    args = parser.parse_args()

    # Input validation moved inside run_transcription_pipeline or specific handlers
    # Keep main_cli simple

    # Run the main processing pipeline
    run_transcription_pipeline(args.pdf_file_path)


if __name__ == "__main__":
    main_cli()