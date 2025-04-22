# -*- coding: utf-8 -*-
"""
Module responsible for generating text embeddings using the chosen model.

Initializes the embedding model client (e.g., OpenAIEmbeddings) and provides
functions to generate vector representations for text chunks.
"""

import sys
from typing import List, Dict, Any, Optional
# Import the specific Langchain embedding class
# Ensure langchain-openai is installed
try:
    from langchain_openai import OpenAIEmbeddings
except ImportError:
    print("Error: langchain-openai library not found. Please install it:", file=sys.stderr)
    print("pip install langchain-openai", file=sys.stderr)
    # Optionally re-raise or exit if the dependency is critical at import time
    # sys.exit(1)
    # For now, allow execution to potentially fail later if called without library
    OpenAIEmbeddings = None

# Import API key loading function (assuming it's needed - OpenAI client often reads env var directly)
# from ..extractor.llm_client import load_api_config # Use relative import if needed

# --- Constants ---
# Define the model name we decided to use
# Could also be loaded from .env if we want flexibility
EMBEDDING_MODEL_NAME = "text-embedding-3-small"
# Specify dimensions if using a model that supports it (like text-embedding-3)
# Smaller dimensions save storage/computation but might lose some nuance.
# Common values: 256, 512, 768, 1024, 1536 (default for small)
# Set to None to use the model's default dimension.
# EMBEDDING_DIMENSIONS = 512 # Example: Reduce dimensions
EMBEDDING_DIMENSIONS = None # Use default (1536 for text-embedding-3-small)

# --- Embedding Model Initialization ---
_embedding_client = None

def get_embedding_client():
    """
    Initializes and returns the Langchain Embedding client configured for OpenAI.

    Reads the OPENAI_API_KEY from environment variables automatically.
    If called multiple times, returns the previously initialized client instance.

    Returns:
        An initialized Langchain OpenAIEmbeddings client instance.

    Raises:
        RuntimeError: If initialization fails (e.g., library not installed, API key missing).
    """
    global _embedding_client
    if _embedding_client is None:
        print("Initializing Embedding client for the first time...")
        if OpenAIEmbeddings is None:
             raise RuntimeError("langchain-openai library is required but not installed.")

        try:
            # OpenAIEmbeddings typically reads OPENAI_API_KEY from env automatically.
            # We might need to load .env explicitly if it's not done elsewhere,
            # but llm_client likely already did. Let's assume key is available.
            # api_key, _, _ = load_api_config() # Load if needed, ensure OPENAI_API_KEY is set

            print(f"  Configuring OpenAIEmbeddings:")
            print(f"    Model: {EMBEDDING_MODEL_NAME}")
            print(f"    Dimensions: {EMBEDDING_DIMENSIONS if EMBEDDING_DIMENSIONS else 'Default'}")

            _embedding_client = OpenAIEmbeddings(
                model=EMBEDDING_MODEL_NAME,
                # openai_api_key=api_key, # Pass explicitly if needed
                dimensions=EMBEDDING_DIMENSIONS if EMBEDDING_DIMENSIONS else None,
                # Add other parameters like chunk_size if needed for batching
            )
            print("Embedding client initialized successfully.")

        except Exception as e:
            error_msg = f"Failed to initialize OpenAI Embedding client: {e}"
            print(error_msg, file=sys.stderr)
            # Check if it's an authentication error (common if key is missing/invalid)
            if "authentication" in str(e).lower():
                 print("  Hint: Ensure OPENAI_API_KEY is set correctly in your .env file.", file=sys.stderr)
            raise RuntimeError(error_msg) from e

    return _embedding_client

# --- Embedding Generation Function ---
def generate_embeddings_for_chunks(rag_chunks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Generates embeddings for the text content of each RAG chunk.

    Modifies the input list of dictionaries by adding an 'embedding' key
    containing the generated vector for each chunk that has text content.

    Args:
        rag_chunks: A list of dictionaries, where each dict represents a chunk
                    and must contain a 'text_content' key with the string to embed.

    Returns:
        The same list of dictionaries, with the 'embedding' key added to each
        dictionary where embedding generation was successful. Chunks without
        text or causing errors might not have the 'embedding' key.

    Raises:
        RuntimeError: If the embedding client cannot be initialized.
        Exception: If errors occur during the embedding API calls.
    """
    if not rag_chunks:
        print("  Embedding Generator: No chunks provided.")
        return []

    print(f"\n--- Generating Embeddings for {len(rag_chunks)} Chunks ---")
    try:
        embedding_client = get_embedding_client()

        # Extract just the text content to send to the embedding model
        texts_to_embed = [
            chunk.get("text_content", "") for chunk in rag_chunks if chunk.get("text_content")
        ]

        if not texts_to_embed:
             print("  No valid text content found in chunks to generate embeddings.")
             return rag_chunks # Return original list, no embeddings added

        print(f"  Sending {len(texts_to_embed)} non-empty text chunks to embedding API...")

        # Generate embeddings in batches (Langchain client handles batching internally)
        # The result is a list of vectors (each vector is a list of floats)
        embeddings = embedding_client.embed_documents(texts_to_embed)

        print(f"  Successfully received {len(embeddings)} embeddings.")
        if embeddings:
             print(f"  Example embedding dimension: {len(embeddings[0])}")

        # --- Add embeddings back to the original chunk dictionaries ---
        # We need to match embeddings back to the correct chunks,
        # accounting for chunks that might have been skipped (empty text).
        embedding_iter = iter(embeddings)
        successful_embeddings = 0
        for chunk in rag_chunks:
            if chunk.get("text_content"): # If this chunk's text was sent for embedding
                try:
                    chunk['embedding'] = next(embedding_iter) # Assign the next embedding
                    successful_embeddings += 1
                except StopIteration:
                    # Should not happen if lengths match, but handle defensively
                    print(f"  Error: Ran out of embeddings while assigning to chunks. Chunk ID: {chunk.get('chunk_id', 'N/A')}", file=sys.stderr)
                    chunk['embedding'] = None # Mark as failed
            else:
                # Chunk had no text content, so no embedding was generated
                chunk['embedding'] = None

        print(f"  Added embeddings to {successful_embeddings} chunks.")
        return rag_chunks

    except RuntimeError as e:
        print(f"Error getting embedding client: {e}", file=sys.stderr)
        raise # Re-raise client initialization errors
    except Exception as e:
        print(f"Error during embedding generation API call: {e}", file=sys.stderr)
        # Decide how to handle API errors - stop everything or allow skipping?
        # For now, re-raise to stop the pipeline
        raise

# Example usage block (for testing when script is run directly)
if __name__ == "__main__":
    print("\n--- Running embedding_generator.py directly for testing ---")
    # Requires .env file with OPENAI_API_KEY

    # Sample RAG chunks (output from formatter.py)
    sample_chunks = [
        {
            "chunk_id": "doc1_p1_c1",
            "text_content": "This is the first chunk of text.",
            "metadata": {"page_number": 1, "source_pdf": "doc1.pdf"}
        },
        {
            "chunk_id": "doc1_p1_c2",
            "text_content": "Este é o segundo pedaço, em português.",
            "metadata": {"page_number": 1, "source_pdf": "doc1.pdf"}
        },
        {
            "chunk_id": "doc1_p2_c3",
            "text_content": "", # Empty chunk
            "metadata": {"page_number": 2, "source_pdf": "doc1.pdf"}
        },
         {
            "chunk_id": "doc1_p2_c4",
            "text_content": "Final chunk with more content to analyze.",
            "metadata": {"page_number": 2, "source_pdf": "doc1.pdf"}
        }
    ]

    print(f"\nInput Chunks: {len(sample_chunks)}")

    try:
        # Generate embeddings (modifies the list in-place)
        chunks_with_embeddings = generate_embeddings_for_chunks(sample_chunks)

        print("\n--- Results ---")
        embedding_count = 0
        for i, chunk in enumerate(chunks_with_embeddings):
            print(f"\nChunk {i+1} (ID: {chunk.get('chunk_id', 'N/A')}):")
            print(f"  Text: '{chunk.get('text_content', '')[:50]}...'")
            embedding = chunk.get('embedding')
            if isinstance(embedding, list):
                print(f"  Embedding Generated: Yes (Dimension: {len(embedding)})")
                # print(f"  Embedding Snippet: {embedding[:5]}...") # Optional: print first few values
                embedding_count += 1
            else:
                print(f"  Embedding Generated: No")

        print(f"\nTotal embeddings generated: {embedding_count}")

    except RuntimeError as e:
         print(f"\nTesting failed due to runtime error: {e}")
    except Exception as e:
         print(f"\nAn unexpected error occurred during testing: {e}")

    print("\n--- Embedding Generator Test Complete ---")