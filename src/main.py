# -*- coding: utf-8 -*-
"""
Main entry point for the Transcritor PDF CLI application.

Orchestrates the workflow by splitting the PDF and then processing each page
using a helper function. Includes logging, optional output saving, validation,
summary, and cleanup. Refactored for clarity.
"""
import argparse
import sys
import os
import json
import asyncio
import logging
from typing import Dict, Any, Optional, List # Added List

# --- Logging Configuration ---
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(name)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# --- Module Imports ---
try:
    import pypdfium2 as pdfium
    from PIL import Image # Import Image here as it's used in helper
except ImportError as e:
    logger.critical(f"Required library not found ({e}). Please install requirements.txt")
    sys.exit(1)

from .input_handler.pdf_splitter import split_pdf_to_pages, TEMP_PAGE_DIR
from .input_handler.loader import load_page_image
from .preprocessor.image_processor import preprocess_image
from .extractor.text_extractor import extract_text_from_image
from .extractor.info_parser import parse_extracted_info
from .output_handler.formatter import format_output_for_rag
from .vectorizer.embedding_generator import generate_embeddings_for_chunks
from .vectorizer.vector_store_handler import add_chunks_to_vector_store

# --- Helper Function for Processing a Single Page ---
def _process_single_page(page_path: str, page_number: int, pdf_file_path: str) -> Dict[str, Any]:
    """
    Processes a single page image: loads, preprocesses, extracts text, parses info.

    Args:
        page_path: Path to the temporary image file for the page.
        page_number: The page number (1-based).
        pdf_file_path: Path to the original PDF (for context/metadata).

    Returns:
        A dictionary containing the processed data for the page, including
        'page_number', 'extracted_text', parsed fields, and potentially an 'error' key.
    """
    logger.info(f"--- Processing Page {page_number} (File: {page_path}) ---")
    page_image: Optional[Image.Image] = None
    processed_page_image: Optional[Image.Image] = None
    extracted_text: Optional[str] = None
    parsed_info: Optional[Dict[str, Any]] = None
    page_result: Dict[str, Any] = { # Initialize result dict for this page
        "page_number": page_number,
        "source_file": pdf_file_path,
        "temp_image_path": page_path,
        "error": None, # Default to no error
        "extracted_text": None,
    }

    try:
        # Step 2: Load Page Image
        logger.info("--- Step 2: Loading Page Image ---")
        page_image = load_page_image(page_path)

        if page_image:
            # Step 3: Preprocess Page Image
            logger.info("--- Step 3: Preprocessing Page Image ---")
            processed_page_image = preprocess_image(page_image)
            page_result["preprocessing_applied"] = True # Mark as applied

            # Step 4: Extract Text from Image
            logger.info("--- Step 4: Extracting Text ---")
            extracted_text = extract_text_from_image(processed_page_image)
            page_result["extracted_text"] = extracted_text if extracted_text else "Extraction Failed"

            # Step 4.5: Parse Structured Information
            if extracted_text:
                logger.info("--- Step 4.5: Parsing Extracted Text ---")
                parsed_info = parse_extracted_info(extracted_text)
                if parsed_info:
                    logger.info("  Successfully parsed structured information.")
                    # Merge parsed info into the page result
                    page_result.update(parsed_info)
                else:
                    logger.warning("  Structured information parsing failed or returned None.")
                    # Keep parsed_info fields as potentially None or default in page_result
            else:
                logger.warning("  Skipping information parsing because text extraction failed.")

    except FileNotFoundError as e:
         logger.error(f"Could not load page image: {e}. Skipping page {page_number}.")
         page_result["error"] = f"File not found: {e}"
         page_result["extracted_text"] = "Loading Error"
    except Exception as page_processing_error:
        logger.error(f"Error processing page {page_number}: {page_processing_error}", exc_info=True)
        page_result["error"] = str(page_processing_error)
        page_result["extracted_text"] = "Processing Error"
    finally:
        # Close image objects for this page
        if page_image:
            try: page_image.close()
            except Exception as e: logger.warning(f"Error closing original image pg {page_number}: {e}")
        if processed_page_image:
            try: processed_page_image.close()
            except Exception as e: logger.warning(f"Error closing processed image pg {page_number}: {e}")

    return page_result


# --- Utility function for cleaning up temporary files ---
def cleanup_temp_files(temp_files: List[Optional[str]]): # Accept Optional[str]
    """Removes the temporary files created during processing."""
    valid_temp_files = [f for f in temp_files if f is not None]
    if not valid_temp_files: return
    logger.info(f"Cleaning up {len(valid_temp_files)} temporary page files...")
    # ...(rest of cleanup logic remains the same)...
    files_removed_count = 0
    for file_path in valid_temp_files:
        if os.path.exists(file_path):
            try: os.remove(file_path); files_removed_count += 1
            except OSError as e: logger.warning(f"Could not remove temp file {file_path}: {e}")
        else: logger.warning(f"Temp file path '{file_path}' not found during cleanup.")
    logger.info(f"Removed {files_removed_count} temporary files.")
    try:
        if os.path.exists(TEMP_PAGE_DIR) and not os.listdir(TEMP_PAGE_DIR):
            os.rmdir(TEMP_PAGE_DIR); logger.info(f"Removed empty temporary directory: {TEMP_PAGE_DIR}")
    except OSError as e: logger.warning(f"Could not remove temp directory {TEMP_PAGE_DIR}: {e}")


# --- Utility function to save output ---
def save_rag_chunks_to_jsonl(rag_chunks: list[dict], output_file_path: str):
    """Saves the list of RAG chunks to a JSON Lines file."""
    logger.info(f"Saving {len(rag_chunks)} RAG chunks to: {output_file_path}")
    # ...(rest of save logic remains the same)...
    try:
        with open(output_file_path, 'w', encoding='utf-8') as f:
            for chunk_data in rag_chunks:
                if 'embedding' in chunk_data and not isinstance(chunk_data['embedding'], list):
                     logger.warning(f"Chunk {chunk_data.get('chunk_id')} has non-list embedding, saving as null.")
                     chunk_data['embedding'] = None
                json_record = json.dumps(chunk_data, ensure_ascii=False)
                f.write(json_record + '\n')
        logger.info("Successfully saved output file.")
    except IOError as e: logger.error(f"Failed to write output file '{output_file_path}': {e}", exc_info=True)
    except TypeError as e: logger.error(f"Failed to serialize chunk data to JSON: {e}", exc_info=True)


# --- Utility function to display summary ---
def display_summary(all_page_results: list[dict], rag_chunks: list[dict], total_pages_in_pdf: int):
    """Displays a summary of the processing results to the console."""
    print("\n" + "="*30 + " Processing Summary " + "="*30)
    # ...(rest of summary logic remains the same)...
    attempted_pages_count = len(all_page_results)
    successful_pages_count = len([p for p in all_page_results if not p.get("error") and p.get("extracted_text") not in [None, "", "Extraction Failed", "Processing Error", "Loading Error"]])
    rag_chunk_count = len(rag_chunks)
    print(f"Total Pages in PDF: {total_pages_in_pdf if total_pages_in_pdf > 0 else 'Unknown'}")
    print(f"Pages Attempted: {attempted_pages_count}")
    print(f"Pages Successfully Processed (Text Extracted/Parsed): {successful_pages_count}")
    print(f"RAG Chunks Generated: {rag_chunk_count}")
    if successful_pages_count > 0:
        print("\n--- Sample Extracted Info (First few successful pages) ---")
        pages_to_show = 3; shown_count = 0
        for page_data in all_page_results:
            if not page_data.get("error") and page_data.get("extracted_text") not in [None, "", "Extraction Failed", "Processing Error", "Loading Error"]:
                if shown_count >= pages_to_show: break
                print(f"\nPage {page_data.get('page_number', '?')}:")
                print(f"  Client Name: {page_data.get('client_name', 'N/A')}")
                print(f"  Document Date: {page_data.get('document_date', 'N/A')}")
                print(f"  Signature Found: {page_data.get('signature_found', 'N/A')}")
                text_snippet = (page_data.get('extracted_text') or "")[:100].replace('\n', ' ') + "..."
                print(f"  Text Snippet: {text_snippet}")
                shown_count += 1
        if shown_count == 0: print("  (No pages with successfully parsed info to display sample)")
    print("="*80)


# --- Main Pipeline Function (async) ---
async def run_transcription_pipeline(pdf_file_path: str, output_file: str | None = None):
    """
    Executes the complete processing pipeline for a given PDF file asynchronously.

    Args:
        pdf_file_path: The path to the input PDF file.
        output_file: Optional path to save the formatted RAG chunks as a JSONL file.
    """
    logger.info(f"Starting transcription pipeline for: {pdf_file_path}")
    if output_file: logger.info(f"Output will be saved to: {output_file}")

    temp_page_paths_generated: List[Optional[str]] = [] # Track all yielded paths
    all_page_results: List[Dict[str, Any]] = [] # Stores results/errors for each page
    rag_chunks: List[Dict[str, Any]] = []
    total_pages_in_pdf = 0

    try:
        # --- Step 1: Split PDF into Pages (and get page count) ---
        logger.info("--- Step 1: Splitting PDF into Pages ---")
        try:
            pdf_doc_check = pdfium.PdfDocument(pdf_file_path)
            total_pages_in_pdf = len(pdf_doc_check)
            pdf_doc_check.close()
            logger.info(f"PDF contains {total_pages_in_pdf} pages.")
        except Exception as e:
            logger.error(f"Could not get page count before splitting: {e}")

        page_path_generator = split_pdf_to_pages(pdf_file_path)

        # --- Page Processing Loop (Refactored) ---
        page_number = 0
        for page_path in page_path_generator:
            page_number += 1
            temp_page_paths_generated.append(page_path) # Track path (or None)

            if page_path is None:
                logger.warning(f"Skipping processing for page {page_number} as splitting/saving failed.")
                all_page_results.append({ # Record the splitting error
                    "page_number": page_number, "error": "Page splitting/saving failed",
                    "extracted_text": "Splitting Error", "source_file": pdf_file_path,
                    "temp_image_path": None
                })
                continue # Skip to next page

            # Call the helper function to process this single page
            page_result = _process_single_page(page_path, page_number, pdf_file_path)
            all_page_results.append(page_result)
        # --- End Page Processing Loop ---

        # Check if any pages were processed successfully before proceeding
        if not any(p for p in all_page_results if not p.get("error")):
             logger.warning("No pages were successfully processed.")
             # Skip formatting, embedding, storage if no pages succeeded
        else:
            # --- Post-Loop Processing ---
            logger.info("--- Step 5: Formatting Output for RAG ---")
            rag_chunks = format_output_for_rag(all_page_results, pdf_file_path)

            if output_file and rag_chunks:
                save_rag_chunks_to_jsonl(rag_chunks, output_file)
            elif output_file:
                 logger.warning(f"Output file '{output_file}' requested, but no RAG chunks generated.")

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

        # --- Display Summary ---
        display_summary(all_page_results, rag_chunks, total_pages_in_pdf)

        logger.info("Pipeline finished successfully.")

    except Exception as pipeline_error:
        logger.critical(f"Pipeline Error: Processing failed. Error: {pipeline_error}", exc_info=True)
        raise # Re-raise to be caught by main_cli
    finally:
        # --- Cleanup ---
        cleanup_temp_files(temp_page_paths_generated)


# --- CLI Argument Parsing and Execution ---
def main_cli():
    """
    Sets up CLI args, performs initial PDF validation, then starts the async pipeline.
    """
    logger.info("--- Transcritor PDF CLI Starting ---")
    parser = argparse.ArgumentParser(description="Process PDF doc...")
    parser.add_argument("pdf_file_path", type=str, help="Path to the PDF file.")
    parser.add_argument("-o", "--output-file", type=str, default=None, help="Optional path to save RAG chunks (.jsonl).")
    args = parser.parse_args()

    pdf_path = args.pdf_file_path
    logger.info(f"Validating input file: {pdf_path}")
    if not os.path.isfile(pdf_path): logger.critical(f"Input Error: File not found: '{pdf_path}'"); sys.exit(1)

    pdf_doc = None
    try:
        pdf_doc = pdfium.PdfDocument(pdf_path)
        logger.info(f"Successfully opened PDF for initial validation ({len(pdf_doc)} pages).")
        pdf_doc.close()
    except pdfium.errors.PasswordError: logger.critical(f"Input Error: PDF '{pdf_path}' is password protected."); sys.exit(1)
    except pdfium.errors.PdfiumError as e: logger.critical(f"Input Error: Failed to open/process PDF '{pdf_path}'. Error: {e}", exc_info=True); sys.exit(1)
    except Exception as e: logger.critical(f"Input Error: Unexpected error validating PDF '{pdf_path}': {e}", exc_info=True); sys.exit(1)

    try:
        logger.info(f"Starting main processing pipeline for: {pdf_path}")
        asyncio.run(run_transcription_pipeline(pdf_path, args.output_file))
        logger.info("--- Transcritor PDF CLI Finished Successfully ---")
    except Exception as e:
        logger.info("--- Transcritor PDF CLI Finished with Errors ---")
        sys.exit(1) # Error already logged within pipeline

if __name__ == "__main__":
    main_cli()