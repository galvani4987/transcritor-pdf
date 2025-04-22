# -*- coding: utf-8 -*-
"""
Main entry point for the Transcritor PDF CLI application.

Orchestrates the workflow: split PDF -> load page -> preprocess page ->
extract text -> parse info -> format output (RAG chunks) -> generate embeddings -> store in DB.
Includes basic logging configuration.
"""
import argparse
import sys
import os
import json
import asyncio
import logging # Import the logging module

# --- Logging Configuration ---
# Configure logging basic settings
# Level: Minimum severity level to log (DEBUG, INFO, WARNING, ERROR, CRITICAL)
# Format: How log messages should look
# Date Format: How the time should be formatted
logging.basicConfig(
    level=logging.INFO, # Log INFO, WARNING, ERROR, CRITICAL
    format='%(asctime)s - %(levelname)s - %(name)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
# Get a logger instance for this module
logger = logging.getLogger(__name__)
# Example: If you want to make library loggers less verbose (e.g., httpx from openai)
# logging.getLogger("httpx").setLevel(logging.WARNING)


# Import functions from our modules
# These imports should happen *after* basicConfig is called if they also use logging
from .input_handler.pdf_splitter import split_pdf_to_pages, TEMP_PAGE_DIR
from .input_handler.loader import load_page_image
from .preprocessor.image_processor import preprocess_image
from .extractor.text_extractor import extract_text_from_image
from .extractor.info_parser import parse_extracted_info
from .output_handler.formatter import format_output_for_rag
from .vectorizer.embedding_generator import generate_embeddings_for_chunks
from .vectorizer.vector_store_handler import add_chunks_to_vector_store

# --- Utility function for cleaning up temporary files ---
def cleanup_temp_files(temp_files: list[str]):
    """Removes the temporary files created during processing."""
    logger.info("Cleaning up temporary page files...")
    files_removed_count = 0
    for file_path in temp_files:
        if file_path and isinstance(file_path, str) and os.path.exists(file_path):
            try:
                os.remove(file_path)
                files_removed_count += 1
            except OSError as e:
                # Log warning but continue cleanup
                logger.warning(f"Could not remove temp file {file_path}: {e}")
        elif file_path:
             logger.warning(f"Temp file path '{file_path}' not found for cleanup.")

    logger.info(f"Removed {files_removed_count} temporary files.")

    try:
        if os.path.exists(TEMP_PAGE_DIR) and not os.listdir(TEMP_PAGE_DIR):
            os.rmdir(TEMP_PAGE_DIR)
            logger.info(f"Removed empty temporary directory: {TEMP_PAGE_DIR}")
    except OSError as e:
        logger.warning(f"Could not remove temp directory {TEMP_PAGE_DIR}: {e}")


# --- Main Pipeline Function (now async) ---
async def run_transcription_pipeline(pdf_file_path: str):
    """
    Executes the complete processing pipeline for a given PDF file asynchronously.

    Args:
        pdf_file_path: The path to the input PDF file.
    """
    logger.info(f"Starting transcription pipeline for: {pdf_file_path}")
    temp_page_paths = []
    all_extracted_data = [] # Stores dicts with info for each page

    try:
        logger.info("--- Step 1: Splitting PDF into Pages ---")
        page_path_generator = split_pdf_to_pages(pdf_file_path) # This function should also use logging

        page_number = 0
        for page_path in page_path_generator:
            page_number += 1
            temp_page_paths.append(page_path)
            logger.info(f"--- Processing Page {page_number} (File: {page_path}) ---")
            page_image = None
            processed_page_image = None
            extracted_text = None
            parsed_info = None

            try:
                logger.info("--- Step 2: Loading Page Image ---")
                page_image = load_page_image(page_path) # This function should also use logging

                if page_image:
                    logger.info("--- Step 3: Preprocessing Page Image ---")
                    processed_page_image = preprocess_image(page_image) # This function should also use logging

                    logger.info("--- Step 4: Extracting Text ---")
                    extracted_text = extract_text_from_image(processed_page_image) # This function should also use logging

                    if extracted_text:
                        logger.info(f"  Successfully extracted text (length: {len(extracted_text)} chars).")
                        logger.info("--- Step 4.5: Parsing Extracted Text ---")
                        parsed_info = parse_extracted_info(extracted_text) # This function should also use logging
                        if parsed_info:
                             logger.info("  Successfully parsed structured information.")
                        else:
                             logger.warning("  Structured information parsing failed or returned None.")
                             parsed_info = {}
                    else:
                        logger.warning("  Text extraction failed for this page.")
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
                 logger.error(f"Could not load page image, file not found: {e}. Skipping page {page_number}.")
                 all_extracted_data.append({
                    "page_number": page_number, "source_file": pdf_file_path,
                    "temp_image_path": page_path, "error": f"File not found: {e}",
                    "extracted_text": "Loading Error",
                 })
            except Exception as page_processing_error:
                logger.error(f"Error processing page {page_number} ({page_path}): {page_processing_error}", exc_info=True) # Log traceback
                all_extracted_data.append({
                    "page_number": page_number, "source_file": pdf_file_path,
                    "temp_image_path": page_path, "error": str(page_processing_error),
                    "extracted_text": "Processing Error",
                })
            finally:
                # Close image objects
                if page_image:
                    try: page_image.close()
                    except Exception as e: logger.warning(f"Error closing original image pg {page_number}: {e}")
                if processed_page_image:
                    try: processed_page_image.close()
                    except Exception as e: logger.warning(f"Error closing processed image pg {page_number}: {e}")


        if not all_extracted_data:
             logger.warning("No data was successfully processed from any page.")
             # Still proceed to cleanup even if no data
        else:
            logger.info("--- Step 5: Formatting Output for RAG ---")
            rag_chunks = format_output_for_rag(all_extracted_data, pdf_file_path) # This function should also use logging

            if rag_chunks:
                logger.info(f"  Generated {len(rag_chunks)} chunks suitable for RAG.")

                logger.info("--- Step 6: Generating Embeddings ---")
                rag_chunks_with_embeddings = generate_embeddings_for_chunks(rag_chunks) # This function should also use logging

                chunks_to_store = [chunk for chunk in rag_chunks_with_embeddings if chunk.get('embedding')]

                if chunks_to_store:
                    logger.info("--- Step 7: Adding Chunks to Vector Store ---")
                    await add_chunks_to_vector_store(chunks_to_store) # This function should also use logging
                else:
                    logger.warning("Skipping database insertion as no chunks had successful embeddings.")
            else:
                logger.warning("No RAG chunks were generated, skipping embedding and storage.")

        logger.info("Pipeline finished successfully.")

    except FileNotFoundError as e:
         logger.critical(f"Pipeline Error: Input file validation failed. {e}")
         # No cleanup needed here as splitting likely failed early
         sys.exit(1) # Exit with error
    except Exception as pipeline_error:
        logger.critical(f"Pipeline Error: An unexpected error occurred during the main pipeline: {pipeline_error}", exc_info=True)
        # Attempt cleanup even if pipeline failed mid-way
        cleanup_temp_files(temp_page_paths)
        sys.exit(1) # Exit with error code after cleanup attempt
    finally:
         # Ensure cleanup happens even if steps after loop fail (but loop itself succeeded)
         if 'pipeline_error' not in locals(): # Check if exception was caught above
            cleanup_temp_files(temp_page_paths)


# --- CLI Argument Parsing and Execution ---
def main_cli():
    """
    Sets up and runs the CLI argument parser, then starts the async pipeline.
    """
    # Note: Logging is configured at the top level before this function runs.
    logger.info("--- Transcritor PDF CLI Starting ---")
    parser = argparse.ArgumentParser(
        description="Process a PDF file of handwritten medical documents, extract information, format for RAG, generate embeddings, and store in DB."
    )
    parser.add_argument(
        "pdf_file_path",
        type=str,
        help="Path to the PDF file to be processed."
    )
    args = parser.parse_args()

    # Run the async pipeline function using asyncio.run()
    try:
        asyncio.run(run_transcription_pipeline(args.pdf_file_path))
        logger.info("--- Transcritor PDF CLI Finished Successfully ---")
    except Exception as e:
        # Catch potential errors bubbled up from the pipeline that weren't handled internally
        # Logging should have happened within run_transcription_pipeline's except block
        logger.critical(f"Pipeline execution failed with unhandled error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main_cli()