# -*- coding: utf-8 -*-
"""
Main entry point for the Transcritor PDF CLI application.

Orchestrates the workflow: split PDF -> load page -> preprocess page ->
extract text -> [TODO: parse info] -> format output -> vectorize & store.
"""
import argparse
import sys
import os

# Import functions from our modules
from .input_handler.pdf_splitter import split_pdf_to_pages, TEMP_PAGE_DIR
from .input_handler.loader import load_page_image
from .preprocessor.image_processor import preprocess_image
# Import the text extraction function
from .extractor.text_extractor import extract_text_from_image
# from .extractor import llm_client, info_parser # info_parser placeholder
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
    all_extracted_data = [] # Stores dicts with info for each page

    try:
        print("\n--- Step 1: Splitting PDF into Pages ---")
        page_path_generator = split_pdf_to_pages(pdf_file_path)

        page_number = 0
        for page_path in page_path_generator:
            page_number += 1
            temp_page_paths.append(page_path)
            print(f"\n--- Processing Page {page_number} (File: {page_path}) ---")
            page_image = None
            processed_page_image = None
            extracted_text = None # Initialize extracted text for this page

            try:
                print(f"--- Step 2: Loading Page Image ---")
                page_image = load_page_image(page_path)

                if page_image:
                    print(f"--- Step 3: Preprocessing Page Image ---")
                    processed_page_image = preprocess_image(page_image)

                    # --- Step 4: Extract Text from Page Image ---
                    print(f"--- Step 4: Extracting Text ---")
                    # Call the text extraction function with the *processed* image
                    extracted_text = extract_text_from_image(processed_page_image)

                    if extracted_text:
                        print(f"  Successfully extracted text (length: {len(extracted_text)} chars).")
                        # --- Step 4.5: Parse Information (Placeholder) ---
                        # TODO: Call info_parser here using extracted_text
                        print("  -> (Placeholder) Parsing specific info (name, date, etc.) from text.")
                        parsed_info = {
                            "client_name": f"Placeholder Name {page_number}",
                            "document_date": f"2025-04-{page_number:02d}", # Dummy date
                            "signature_found": (page_number % 2 == 0), # Dummy boolean
                            "relevant_illness": f"Placeholder Illness {page_number}"
                        }
                    else:
                        print("  Text extraction failed for this page.")
                        parsed_info = {} # Empty dict if text extraction failed

                    # Store results for this page
                    page_data = {
                        "page_number": page_number,
                        "source_file": pdf_file_path,
                        "temp_image_path": page_path,
                        "preprocessing_applied": True, # Or get status from preprocess_image
                        "extracted_text": extracted_text if extracted_text else "Extraction Failed",
                        **parsed_info # Add parsed info fields
                    }
                    all_extracted_data.append(page_data)

            except FileNotFoundError as e:
                 print(f"  Error: Could not load page image, file not found: {e}. Skipping page {page_number}.", file=sys.stderr)
            except Exception as page_processing_error:
                print(f"  Error processing page {page_number} ({page_path}): {page_processing_error}", file=sys.stderr)
                # Store minimal info even if page processing fails mid-way
                all_extracted_data.append({
                    "page_number": page_number,
                    "source_file": pdf_file_path,
                    "temp_image_path": page_path,
                    "error": str(page_processing_error),
                    "extracted_text": "Processing Error",
                })
            finally:
                # Close image objects
                if page_image: page_image.close()
                if processed_page_image: processed_page_image.close()


        if not all_extracted_data:
             print("\nWarning: No data was successfully processed from any page.", file=sys.stderr)

        # --- Step 5: Format Overall Output (Placeholder) ---
        print("\n--- Step 5: Formatting Output ---")
        # formatted_output = formatter.format_output(all_extracted_data, pdf_file_path) # TODO
        print("  -> (Placeholder) Formatting logic here.")
        formatted_output = all_extracted_data
        print("  Formatted Output (Placeholder - First page data snippet):")
        if formatted_output:
            first_page_data = formatted_output[0]
            print(f"    Page {first_page_data.get('page_number', '?')}:")
            print(f"      Text: {first_page_data.get('extracted_text', 'N/A')[:80]}...")
            print(f"      Name: {first_page_data.get('client_name', 'N/A')}")
            print(f"      Date: {first_page_data.get('document_date', 'N/A')}")
        else:
            print("    No data to display.")


        # --- Step 6: Vectorize and Store (Placeholder) ---
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
         # Cleanup only if pipeline finished without top-level exceptions
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