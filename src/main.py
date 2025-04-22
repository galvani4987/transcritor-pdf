# -*- coding: utf-8 -*-
"""
Main entry point for the Transcritor PDF CLI application.

Orchestrates the workflow: split PDF -> load page -> preprocess page ->
extract text -> parse info -> format output (RAG chunks) -> [TODO: vectorize & store].
"""
import argparse
import sys
import os
import json # Import json for potentially printing the output

# Import functions from our modules
from .input_handler.pdf_splitter import split_pdf_to_pages, TEMP_PAGE_DIR
from .input_handler.loader import load_page_image
from .preprocessor.image_processor import preprocess_image
from .extractor.text_extractor import extract_text_from_image
from .extractor.info_parser import parse_extracted_info
# Import the RAG formatter function
from .output_handler.formatter import format_output_for_rag
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
            extracted_text = None
            parsed_info = None

            try:
                print(f"--- Step 2: Loading Page Image ---")
                page_image = load_page_image(page_path)

                if page_image:
                    print(f"--- Step 3: Preprocessing Page Image ---")
                    processed_page_image = preprocess_image(page_image)

                    print(f"--- Step 4: Extracting Text ---")
                    extracted_text = extract_text_from_image(processed_page_image)

                    if extracted_text:
                        print(f"--- Step 4.5: Parsing Extracted Text ---")
                        parsed_info = parse_extracted_info(extracted_text)
                        if parsed_info:
                             print("  Successfully parsed structured information.")
                        else:
                             print("  Structured information parsing failed or returned None.")
                             parsed_info = {}
                    else:
                        print("  Skipping information parsing because text extraction failed.")
                        parsed_info = {}

                    page_data = {
                        "page_number": page_number,
                        "source_file": pdf_file_path,
                        "temp_image_path": page_path,
                        "preprocessing_applied": True,
                        "extracted_text": extracted_text if extracted_text else "Extraction Failed",
                        **(parsed_info if parsed_info else {})
                    }
                    all_extracted_data.append(page_data)

            except FileNotFoundError as e:
                 print(f"  Error: Could not load page image, file not found: {e}. Skipping page {page_number}.", file=sys.stderr)
                 all_extracted_data.append({
                    "page_number": page_number, "source_file": pdf_file_path,
                    "temp_image_path": page_path, "error": f"File not found: {e}",
                    "extracted_text": "Loading Error",
                 })
            except Exception as page_processing_error:
                print(f"  Error processing page {page_number} ({page_path}): {page_processing_error}", file=sys.stderr)
                all_extracted_data.append({
                    "page_number": page_number, "source_file": pdf_file_path,
                    "temp_image_path": page_path, "error": str(page_processing_error),
                    "extracted_text": "Processing Error",
                })
            finally:
                if page_image: page_image.close()
                if processed_page_image: processed_page_image.close()


        if not all_extracted_data:
             print("\nWarning: No data was successfully processed from any page.", file=sys.stderr)
             # Exit early if no data? Or continue to allow cleanup? Continuing for now.

        # --- Step 5: Format Output for RAG ---
        print("\n--- Step 5: Formatting Output for RAG ---")
        # Call the formatter function with the collected page data
        rag_chunks = format_output_for_rag(all_extracted_data, pdf_file_path)

        # Print a summary or the first chunk for verification
        print("  Output formatting complete.")
        if rag_chunks:
            print(f"  Generated {len(rag_chunks)} chunks suitable for RAG.")
            print("  Example RAG Chunk (First Chunk):")
            # Use json.dumps for pretty printing the dictionary
            print(json.dumps(rag_chunks[0], indent=2, ensure_ascii=False))
            # TODO: Add option to save rag_chunks to a file (e.g., jsonl)
        else:
            print("  No RAG chunks were generated.")


        # --- Step 6: Vectorize and Store (Placeholder) ---
        print("\n--- Step 6: Vectorizing and Storing ---")
        # This step will take rag_chunks as input
        # vectorize_and_store(rag_chunks) # TODO
        print("  -> (Placeholder) Vectorization logic using rag_chunks here.")

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
        description="Process a PDF file of handwritten medical documents, extract information, format for RAG, and optionally vectorize."
    )
    parser.add_argument(
        "pdf_file_path",
        type=str,
        help="Path to the PDF file to be processed."
    )
    # Example: Add optional argument to save output
    # parser.add_argument(
    #     "-o", "--output-file",
    #     type=str,
    #     help="Path to save the formatted RAG chunks (e.g., output.jsonl)."
    # )
    args = parser.parse_args()
    run_transcription_pipeline(args.pdf_file_path) # Pass output_file arg if added


if __name__ == "__main__":
    main_cli()