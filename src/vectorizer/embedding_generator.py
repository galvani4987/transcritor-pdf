# -*- coding: utf-8 -*-
"""
Module responsible for generating text embeddings using the chosen model.

Initializes the embedding model client (e.g., OpenAIEmbeddings) and provides
functions to generate vector representations for text chunks. Includes logging.
"""

import sys
import logging # Import logging
from typing import List, Dict, Any, Optional
# Import the specific Langchain embedding class
try:
    from langchain_openai import OpenAIEmbeddings
except ImportError:
    # Log critical error if dependency is missing
    logging.critical("langchain-openai library not found. Please install it: pip install langchain-openai")
    sys.exit(1)

# Get a logger instance for this module
logger = logging.getLogger(__name__)

# --- Constants ---
EMBEDDING_MODEL_NAME = "text-embedding-3-small"
EMBEDDING_DIMENSIONS = None # Use default (1536 for text-embedding-3-small)

# --- Embedding Model Initialization ---
_embedding_client = None

def get_embedding_client():
    """
    Initializes and returns the Langchain Embedding client configured for OpenAI.

    Returns:
        An initialized Langchain OpenAIEmbeddings client instance.
    Raises:
        RuntimeError: If initialization fails.
    """
    global _embedding_client
    if _embedding_client is None:
        logger.info("Initializing Embedding client for the first time...")
        if OpenAIEmbeddings is None:
             # This case should ideally not be reached due to check at import time
             logger.critical("OpenAIEmbeddings class not available (import failed).")
             raise RuntimeError("langchain-openai library is required but failed to import.")

        try:
            logger.info("Configuring OpenAIEmbeddings:")
            logger.info(f"  Model: {EMBEDDING_MODEL_NAME}")
            logger.info(f"  Dimensions: {EMBEDDING_DIMENSIONS if EMBEDDING_DIMENSIONS else 'Default'}")

            _embedding_client = OpenAIEmbeddings(
                model=EMBEDDING_MODEL_NAME,
                dimensions=EMBEDDING_DIMENSIONS if EMBEDDING_DIMENSIONS else None,
            )
            logger.info("Embedding client initialized successfully.")

        except Exception as e:
            logger.critical(f"Failed to initialize OpenAI Embedding client: {e}", exc_info=True)
            if "authentication" in str(e).lower():
                 logger.error("Hint: Ensure OPENAI_API_KEY is set correctly in your .env file.")
            raise RuntimeError(f"Failed to initialize OpenAI Embedding client: {e}") from e

    return _embedding_client

# --- Embedding Generation Function ---
def generate_embeddings_for_chunks(rag_chunks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Generates embeddings for the text content of each RAG chunk.

    Modifies the input list by adding an 'embedding' key to each chunk dict.

    Args:
        rag_chunks: List of chunk dictionaries with 'text_content'.

    Returns:
        The modified list of chunk dictionaries with 'embedding' added.
    Raises:
        RuntimeError: If the embedding client cannot be initialized.
        Exception: If errors occur during the embedding API calls.
    """
    if not rag_chunks:
        logger.warning("Embedding Generator: No chunks provided.")
        return []

    logger.info(f"--- Generating Embeddings for {len(rag_chunks)} Chunks ---")
    try:
        embedding_client = get_embedding_client() # Handles initialization logging

        texts_to_embed = [
            chunk.get("text_content", "") for chunk in rag_chunks if chunk.get("text_content")
        ]

        if not texts_to_embed:
             logger.warning("No valid text content found in chunks to generate embeddings.")
             # Add 'embedding': None to all chunks for consistency downstream?
             for chunk in rag_chunks: chunk['embedding'] = None
             return rag_chunks

        logger.info(f"Sending {len(texts_to_embed)} non-empty text chunks to embedding API...")

        # Generate embeddings (Langchain handles batching)
        embeddings = embedding_client.embed_documents(texts_to_embed)

        logger.info(f"Successfully received {len(embeddings)} embeddings.")
        if embeddings:
             logger.debug(f"Example embedding dimension: {len(embeddings[0])}") # Log dimension at debug

        # Add embeddings back to the original chunk dictionaries
        embedding_iter = iter(embeddings)
        successful_embeddings = 0
        skipped_embeddings = 0
        for chunk in rag_chunks:
            if chunk.get("text_content"): # If text was sent
                try:
                    chunk['embedding'] = next(embedding_iter)
                    successful_embeddings += 1
                except StopIteration:
                    logger.error(f"Ran out of embeddings while assigning to chunks. Chunk ID: {chunk.get('chunk_id', 'N/A')}")
                    chunk['embedding'] = None
                    skipped_embeddings += 1
            else:
                # Chunk had no text content
                chunk['embedding'] = None
                skipped_embeddings += 1

        logger.info(f"Added embeddings to {successful_embeddings} chunks.")
        if skipped_embeddings > 0:
            logger.warning(f"Skipped embedding assignment for {skipped_embeddings} chunks (no text or error).")
        return rag_chunks

    except RuntimeError as e:
        # Error from get_embedding_client already logged
        raise # Re-raise client initialization errors
    except Exception as e:
        logger.error(f"Error during embedding generation API call: {e}", exc_info=True)
        # Decide handling: stop or mark chunks as failed? Re-raising for now.
        raise

# Example usage block (for testing when script is run directly)
if __name__ == "__main__":
    # Configure logging for test run
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(name)s - %(message)s')
    logger.info("--- Running embedding_generator.py directly for testing ---")
    logger.info("Requires .env file with OPENAI_API_KEY")

    # Sample RAG chunks
    sample_chunks = [
        {"chunk_id": "doc1_p1_c1", "text_content": "This is the first chunk.", "metadata": {}},
        {"chunk_id": "doc1_p1_c2", "text_content": "Este é o segundo pedaço.", "metadata": {}},
        {"chunk_id": "doc1_p2_c3", "text_content": "", "metadata": {}}, # Empty
        {"chunk_id": "doc1_p2_c4", "text_content": "Final chunk.", "metadata": {}}
    ]
    logger.info(f"Input Chunks: {len(sample_chunks)}")

    try:
        chunks_with_embeddings = generate_embeddings_for_chunks(sample_chunks)
        logger.info("--- Results ---")
        embedding_count = 0
        for i, chunk in enumerate(chunks_with_embeddings):
            embedding = chunk.get('embedding')
            status = "Yes" if isinstance(embedding, list) else "No"
            dim = f"(Dim: {len(embedding)})" if isinstance(embedding, list) else ""
            logger.info(f"Chunk {i+1} (ID: {chunk.get('chunk_id', 'N/A')}): Embedding Generated: {status} {dim}")
            if status == "Yes": embedding_count += 1
        logger.info(f"Total embeddings generated: {embedding_count}")

    except RuntimeError as e:
         logger.error(f"Testing failed due to runtime error: {e}")
    except Exception as e:
         logger.error(f"An unexpected error occurred during testing: {e}", exc_info=True)

    logger.info("--- Embedding Generator Test Complete ---")