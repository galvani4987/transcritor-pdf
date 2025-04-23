# -*- coding: utf-8 -*-
"""
Main entry point for the Transcritor PDF CLI application.

Orchestrates the workflow: split PDF -> load page -> preprocess page ->
extract text -> parse info -> format output (RAG chunks) -> generate embeddings -> store in DB.
Includes basic logging configuration, optional output file saving, and initial PDF validation.
"""
import argparse
import sys
import os
import json
import asyncio
import logging
# Import pypdfium2 for initial validation
try:
    import pypdfium2 as pdfium
except ImportError:
    logging.critical("pypdfium2 library not found. Please install it: pip install pypdfium2")
    sys.exit(1)

# --- Logging Configuration ---
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(name)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# --- Module Imports ---
# Imports moved after initial validation where possible
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


# --- Main Pipeline Function (async) ---
async def run_transcription_pipeline(pdf_file_path: str, output_file: str | None = None):
    """
    Executes the complete processing pipeline for a given PDF file asynchronously.

    Args:
        pdf_file_path: The path to the input PDF file.
        output_file: Optional path to save the formatted RAG chunks as a JSONL file.
    """
    logger.info(f"Starting transcription pipeline for: {pdf_file_path}")
    if output_file:
        logger.info(f"Output will be saved to: {output_file}")

    temp_page_paths = []
    all_extracted_data = []
    rag_chunks = []

    try:
        logger.info("--- Step 1: Splitting PDF into Pages ---")
        page_path_generator = split_pdf_to_pages(pdf_file_path)

        page_number = 0
        for page_path in page_path_generator:
            page_number += 1
            temp_page_paths.append(page_path)
            logger.info(f"--- Processing Page {page_number} (File: {page_path}) ---")
            page_image = None; processed_page_image = None; extracted_text = None; parsed_info = None

            try:
                logger.info("--- Step 2: Loading Page Image ---")
                page_image = load_page_image(page_path)

                if page_image:
                    logger.info("--- Step 3: Preprocessing Page Image ---")
                    processed_page_image = preprocess_image(page_image)

                    logger.info("--- Step 4: Extracting Text ---")
                    extracted_text = extract_text_from_image(processed_page_image)

                    if extracted_text:
                        logger.info("--- Step 4.5: Parsing Extracted Text ---")
                        parsed_info = parse_extracted_info(extracted_text)
                        if not parsed_info: parsed_info = {}
                    else:
                        logger.warning("  Text extraction failed for this page.")
                        parsed_info = {}

                    page_data = {
                        "page_number": page_number, "source_file": pdf_file_path,
                        "temp_image_path": page_path, "preprocessing_applied": True,
                        "extracted_text": extracted_text if extracted_text else "Extraction Failed",
                        **(parsed_info if parsed_info else {})
                    }
                    all_extracted_data.append(page_data)

            except FileNotFoundError as e:
                 logger.error(f"Could not load page image: {e}. Skipping page {page_number}.")
                 all_extracted_data.append({"page_number": page_number, "error": f"File not found: {e}", "extracted_text": "Loading Error"})
            except Exception as page_processing_error:
                logger.error(f"Error processing page {page_number}: {page_processing_error}", exc_info=True)
                all_extracted_data.append({"page_number": page_number, "error": str(page_processing_error), "extracted_text": "Processing Error"})
            finally:
                if page_image: page_image.close()
                if processed_page_image: processed_page_image.close()


        if not all_extracted_data:
             logger.warning("No data was successfully processed from any page.")
        else:
            logger.info("--- Step 5: Formatting Output for RAG ---")
            rag_chunks = format_output_for_rag(all_extracted_data, pdf_file_path)

            if output_file and rag_chunks:
                save_rag_chunks_to_jsonl(rag_chunks, output_file)
            elif output_file:
                 logger.warning(f"Output file '{output_file}' requested, but no RAG chunks were generated.")

            if rag_chunks:
                logger.info(f"  Generated {len(rag_chunks)} chunks suitable for RAG.")
                logger.info("--- Step 6: Generating Embeddings ---")
                rag_chunks_with_embeddings = generate_embeddings_for_chunks(rag_chunks)
                chunks_to_store = [chunk for chunk in rag_chunks_with_embeddings if chunk.get('embedding')]

                if chunks_to_store:
                    logger.info("--- Step 7: Adding Chunks to Vector Store ---")
                    await add_chunks_to_vector_store(chunks_to_store)
                else:
                    logger.warning("Skipping database insertion as no chunks had successful embeddings.")
            else:
                logger.warning("No RAG chunks were generated, skipping embedding and storage.")

        logger.info("Pipeline finished successfully.")

    # Keep general exception handler for unexpected errors within the pipeline
    except Exception as pipeline_error:
        # Log the error that occurred *during* the pipeline steps
        logger.critical(f"Pipeline Error: An unexpected error occurred during processing: {pipeline_error}", exc_info=True)
        # Re-raise the exception so it's caught by the outer handler in main_cli,
        # which will trigger cleanup and exit.
        raise
    # No finally block here for cleanup, as it should be handled by the caller (main_cli)


# --- Utility function to save output ---
def save_rag_chunks_to_jsonl(rag_chunks: list[dict], output_file_path: str):
    """Saves the list of RAG chunks to a JSON Lines file."""
    logger.info(f"Saving {len(rag_chunks)} RAG chunks to: {output_file_path}")
    try:
        with open(output_file_path, 'w', encoding='utf-8') as f:
            for chunk_data in rag_chunks:
                json_record = json.dumps(chunk_data, ensure_ascii=False)
                f.write(json_record + '\n')
        logger.info("Successfully saved output file.")
    except IOError as e:
        logger.error(f"Failed to write output file '{output_file_path}': {e}", exc_info=True)
    except TypeError as e:
         logger.error(f"Failed to serialize chunk data to JSON: {e}", exc_info=True)


# --- CLI Argument Parsing and Execution ---
def main_cli():
    """
    Sets up CLI args, performs initial PDF validation, then starts the async pipeline.
    """
    logger.info("--- Transcritor PDF CLI Starting ---")
    parser = argparse.ArgumentParser(
        description="Process a PDF file, extract info, format for RAG, generate embeddings, and store in DB."
    )
    parser.add_argument(
        "pdf_file_path",
        type=str,
        help="Path to the PDF file to be processed."
    )
    parser.add_argument(
        "-o", "--output-file",
        type=str,
        default=None,
        help="Optional path to save the formatted RAG chunks as a JSON Lines (.jsonl) file."
    )
    args = parser.parse_args()

    # --- Initial Input Validation ---
    pdf_path = args.pdf_file_path
    logger.info(f"Validating input file: {pdf_path}")

    if not os.path.isfile(pdf_path):
        logger.critical(f"Input Error: File not found at '{pdf_path}'")
        sys.exit(1)

    # --- Attempt to open PDF early to catch basic errors ---
    pdf_doc = None
    try:
        # Try opening with pypdfium2 (catches password errors, basic corruption)
        pdf_doc = pdfium.PdfDocument(pdf_path)
        logger.info(f"Successfully opened PDF for initial validation ({len(pdf_doc)} pages).")
        # We don't need to keep it open, just check if it *can* be opened.
        pdf_doc.close()
    except pdfium.errors.PasswordError:
        logger.critical(f"Input Error: PDF file '{pdf_path}' is password protected.")
        sys.exit(1)
    except pdfium.errors.PdfiumError as e:
        # Catch other pypdfium2 errors (e.g., format errors, corruption)
        logger.critical(f"Input Error: Failed to open or process PDF '{pdf_path}' with pypdfium2. Error: {e}", exc_info=True)
        sys.exit(1)
    except Exception as e:
        # Catch any other unexpected error during the open attempt
        logger.critical(f"Input Error: An unexpected error occurred while validating PDF '{pdf_path}': {e}", exc_info=True)
        if pdf_doc: pdf_doc.close() # Ensure close if partially opened
        sys.exit(1)

    # --- Run the Async Pipeline ---
    # If initial validation passed, proceed with the main processing.
    temp_files_list = [] # Define list here to be accessible in finally
    try:
        logger.info(f"Starting main processing pipeline for: {pdf_path}")
        # Pass output file argument to the pipeline function
        # asyncio.run will execute the async function and block until it completes
        # We need to capture the temp_files list if the pipeline modifies it directly
        # Modification: Let run_transcription_pipeline return temp_files list?
        # Simpler approach: rely on the finally block of run_transcription_pipeline (if added back)
        # OR handle cleanup here based on TEMP_PAGE_DIR? Let's assume cleanup is handled within run_transcription_pipeline for now.
        asyncio.run(run_transcription_pipeline(pdf_path, args.output_file))
        logger.info("--- Transcritor PDF CLI Finished Successfully ---")
    except Exception as e:
        # Catch errors bubbled up from the pipeline (already logged)
        logger.info("--- Transcritor PDF CLI Finished with Errors ---")
        # Cleanup might have already been attempted in run_transcription_pipeline's except block
        # We could add another cleanup attempt here just in case, but it might be redundant.
        sys.exit(1)


if __name__ == "__main__":
    main_cli()