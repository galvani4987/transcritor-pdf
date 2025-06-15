# -*- coding: utf-8 -*-
"""
Main entry point for the Transcritor PDF API.
"""
import logging
from fastapi import FastAPI

# --- FastAPI App Initialization ---
app = FastAPI(
    title="Transcritor PDF API",
    description="API para processar arquivos PDF, extrair texto e informações estruturadas, e preparar dados para RAG.",
    version="0.1.0"
)

# --- Logging Configuration ---
# Basic logging setup, can be expanded later (e.g., from config file)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(name)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# --- Root Endpoint ---
@app.get("/")
async def root():
    """
    Root endpoint providing a welcome message.
    """
    logger.info("Root endpoint '/' was called.")
    return {"message": "Welcome to the Transcritor PDF API"}

# --- Placeholder for future imports and pipeline logic ---
# from .input_handler.pdf_splitter import split_pdf_to_pages, TEMP_PAGE_DIR
# from .input_handler.loader import load_page_image
# from .preprocessor.image_processor import preprocess_image
# from .extractor.text_extractor import extract_text_from_image
# from .extractor.info_parser import parse_extracted_info
# from .output_handler.formatter import format_output_for_rag
# from .vectorizer.embedding_generator import generate_embeddings_for_chunks
# from .vectorizer.vector_store_handler import add_chunks_to_vector_store

# --- Placeholder for the main pipeline function (to be refactored and called by API endpoints) ---
# async def run_transcription_pipeline(pdf_content: bytes, filename: str):
#     logger.info(f"Placeholder: run_transcription_pipeline called for {filename}")
#     # ... core processing logic will go here ...
#     return {"filename": filename, "status": "processing_placeholder"}

# To run this FastAPI app (ensure uvicorn is installed: pip install "uvicorn[standard]"):
# uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
# Or from the project root, if src is in PYTHONPATH:
# python -m uvicorn src.main:app --reload --host 0.0.0.0 --port 8000