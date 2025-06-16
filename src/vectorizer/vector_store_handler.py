# -*- coding: utf-8 -*-
"""Handles interaction with the vector store (PostgreSQL + pgvector) using asyncpg.
Simplified internal error handling. Includes logging.
"""

import os
import sys
import asyncio
import json
import logging
from typing import List, Dict, Any, Optional
try:
    import asyncpg
except ImportError:
    logging.critical("asyncpg library not found. Please install it: pip install asyncpg")
    sys.exit(1)
from dotenv import load_dotenv, find_dotenv

logger = logging.getLogger(__name__)

def load_db_config() -> Dict[str, Optional[str]]:
    """Loads PostgreSQL connection parameters from environment variables."""
    env_path = find_dotenv()
    if env_path: logger.info(f"Loading database config from: {env_path}"); load_dotenv(dotenv_path=env_path, override=True)
    else: logger.warning(".env file not found for database config.")
    config = {
        "host": os.getenv("DB_HOST", "localhost"), "port": int(os.getenv("DB_PORT", 5432)),
        "database": os.getenv("DB_NAME"), "user": os.getenv("DB_USER"), "password": os.getenv("DB_PASSWORD"),
    }
    if not config["database"]: logger.warning("DB_NAME not found in environment variables.")
    if not config["user"]: logger.warning("DB_USER not found in environment variables.")
    if not config["password"]: logger.warning("DB_PASSWORD not found in environment variables.")
    logger.info(f"DB Config Loaded: Host={config['host']}, Port={config['port']}, DB={config['database']}, User={config['user']}")
    return config

async def add_chunks_to_vector_store(rag_chunks: List[Dict[str, Any]]):
    """Adds or updates text chunks, metadata, and embeddings in PostgreSQL using asyncpg.

    Connects asynchronously, starts a transaction, and attempts to upsert each
    valid chunk. If any upsert fails due to a database error, the entire
    transaction is rolled back and ConnectionError is raised.

    Args:
        rag_chunks: List of chunk dictionaries with required keys.
    Raises:
        ConnectionError: If credentials missing, connection fails, or DB operation fails.
        ValueError: If chunk data formatting fails (logged as warning, chunk skipped).
        Exception: For other unexpected errors.
    """
    if not rag_chunks: logger.warning("Vector Store Handler: No chunks provided."); return

    logger.info(f"--- Adding {len(rag_chunks)} Chunks to Vector Store (asyncpg) ---")
    db_config = load_db_config()
    conn: Optional[asyncpg.Connection] = None
    inserted_count = 0
    skipped_count = 0

    if not all([db_config["database"], db_config["user"], db_config["password"]]):
         error_msg = "Database connection details missing in .env (DB_NAME, DB_USER, DB_PASSWORD)."
         logger.critical(error_msg); raise ConnectionError(error_msg)

    try:
        logger.info(f"Connecting to PostgreSQL database '{db_config['database']}' on {db_config['host']}...")
        conn = await asyncpg.connect(**db_config)
        logger.info("Database connection successful (asyncpg).")

        table_name = "documents" # Changed from os.getenv("DB_VECTOR_TABLE", "your_vector_table")
        # chunk_id_col, text_col, metadata_col are implicitly correct. vector_col changed.
        # For simplicity, direct usage in query string is preferred over maintaining these variables if fixed.

        insert_query = f"""
            INSERT INTO {table_name} (chunk_id, text_content, metadata, embedding)
            VALUES ($1, $2, $3, $4) ON CONFLICT (chunk_id) DO UPDATE SET
            text_content=EXCLUDED.text_content, metadata=EXCLUDED.metadata, embedding=EXCLUDED.embedding;
        """
        logger.info(f"Preparing to insert/update data into table '{table_name}'...")

        # --- Start Transaction ---
        async with conn.transaction():
            logger.debug("Transaction started.")
            for chunk in rag_chunks:
                chunk_id, text_content, metadata, embedding = (
                    chunk.get("chunk_id"), chunk.get("text_content"), chunk.get("metadata"), chunk.get("embedding")
                )
                if not chunk_id or not text_content or metadata is None or embedding is None:
                    logger.warning(f"Skipping chunk ID '{chunk_id}' due to missing data."); skipped_count += 1; continue
                try:
                    metadata_to_insert = metadata # Try passing dict directly
                    if isinstance(embedding, list) and all(isinstance(x, (int, float)) for x in embedding):
                        embedding_to_insert = embedding # Try passing list directly
                    else: raise ValueError("Invalid embedding format")
                except Exception as fmt_e:
                    logger.warning(f"Skipping chunk ID '{chunk_id}' due to data formatting error: {fmt_e}", exc_info=True)
                    skipped_count += 1; continue

                # --- Execute Query (Inner try removed) ---
                # Let asyncpg.PostgresError propagate to the outer handler if execute fails
                logger.debug(f"Executing upsert for chunk ID: {chunk_id}")
                await conn.execute(insert_query, chunk_id, text_content, metadata_to_insert, embedding_to_insert)
                inserted_count += 1
            # Transaction commits automatically if loop finishes without error
            logger.info(f"Transaction commit successful. Added/Updated {inserted_count} chunks.")

        if skipped_count > 0: logger.warning(f"Skipped {skipped_count} chunks due to validation/formatting.")

    except (asyncpg.PostgresError, OSError) as db_error:
        # Catch connection errors OR database errors propagated from transaction
        logger.critical(f"Database connection or operation error: {db_error}", exc_info=True)
        # Wrap and raise ConnectionError for unified handling upstream
        raise ConnectionError(f"Database connection or operation failed: {db_error}") from db_error
    except Exception as e:
        logger.critical(f"An unexpected error occurred: {e}", exc_info=True)
        raise # Re-raise other unexpected errors
    finally:
        if conn and not conn.is_closed(): await conn.close(); logger.info("Database connection closed.")

# Example usage block (remains the same)
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(name)s - %(message)s')
    logger.info("--- Running vector_store_handler.py (asyncpg) directly for testing ---")
    logger.warning("This test block WILL attempt to connect to and write to the database.")
    embedding_dim = 1536
    sample_rag_chunks_with_embeddings = [
        {"chunk_id": "async_test_001", "text_content": "Async test chunk 1.", "metadata": {"s": "t1a"}, "embedding": [0.5] * embedding_dim},
        {"chunk_id": "async_test_002", "text_content": "Async test chunk 2.", "metadata": {"s": "t2a"}, "embedding": [0.6] * embedding_dim}
    ]
    logger.info(f"Sample Chunks to Add/Update: {len(sample_rag_chunks_with_embeddings)}")
    confirm = input("\nProceed with test database insertion/update? (yes/no): ")
    if confirm.lower() == 'yes':
        logger.info("Proceeding with test database operation...")
        try: asyncio.run(add_chunks_to_vector_store(sample_rag_chunks_with_embeddings))
        except ConnectionError as e: logger.error(f"Test failed due to connection error: {e}")
        except Exception as e: logger.error(f"An unexpected error occurred during testing: {e}", exc_info=True)
        else: logger.info("Test database operation process completed (check database).")
    else: logger.info("Test database operation cancelled by user.")
    logger.info("--- Vector Store Handler Test Complete ---")