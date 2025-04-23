# -*- coding: utf-8 -*-
"""Handles interaction with the vector store (PostgreSQL + pgvector) using asyncpg.

Connects asynchronously to the PostgreSQL database, formats data, and inserts
or updates text chunks, metadata, and embeddings using the asyncpg driver.
Aligns with modern async Python practices. Includes logging.
"""

import os
import sys
import asyncio
import json
import logging
from typing import List, Dict, Any, Optional
# Import asyncpg driver
try:
    import asyncpg
    # Optional: Import pgvector asyncpg extension if needed for specific type handling
    # from asyncpg.contrib.pgvector.vector import register_vector
except ImportError:
    logging.critical("asyncpg library not found. Please install it: pip install asyncpg")
    sys.exit(1)

# Import dotenv to load environment variables
from dotenv import load_dotenv, find_dotenv

# Get a logger instance for this module
logger = logging.getLogger(__name__)

# --- Database Configuration ---
def load_db_config() -> Dict[str, Optional[str]]:
    """Loads PostgreSQL connection parameters from environment variables.

    Reads DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD from .env file
    or system environment. Logs warnings if mandatory variables are missing.

    Returns:
        A dictionary containing the database connection parameters.
    """
    env_path = find_dotenv()
    if env_path:
        logger.info(f"Loading database config from: {env_path}")
        load_dotenv(dotenv_path=env_path, override=True)
    else:
        logger.warning(".env file not found for database config.")

    config = {
        "host": os.getenv("DB_HOST", "localhost"),
        "port": int(os.getenv("DB_PORT", 5432)), # asyncpg expects int for port
        "database": os.getenv("DB_NAME"),
        "user": os.getenv("DB_USER"),
        "password": os.getenv("DB_PASSWORD"),
    }
    if not config["database"]: logger.warning("DB_NAME not found in environment variables.")
    if not config["user"]: logger.warning("DB_USER not found in environment variables.")
    if not config["password"]: logger.warning("DB_PASSWORD not found in environment variables.")

    logger.info(f"DB Config Loaded: Host={config['host']}, Port={config['port']}, "
                f"DB={config['database']}, User={config['user']}")
    return config

# --- Database Interaction (Using asyncpg) ---
async def add_chunks_to_vector_store(rag_chunks: List[Dict[str, Any]]):
    """Adds or updates text chunks, metadata, and embeddings in PostgreSQL using asyncpg.

    Establishes an asynchronous connection to the database. Iterates through
    the provided RAG chunks, formats data, and executes an asynchronous
    `INSERT ... ON CONFLICT DO UPDATE` query for each valid chunk within a
    single transaction.

    Args:
        rag_chunks: A list of dictionaries representing chunks, each expected
                    to have 'chunk_id', 'text_content', 'metadata', 'embedding'.

    Raises:
        ConnectionError: If database credentials are missing or connection fails.
        ValueError: If chunk data formatting fails. Currently logs warnings and skips.
        asyncpg.exceptions.PostgresError: For database errors during the operation.
        Exception: For other unexpected errors.
    """
    if not rag_chunks:
        logger.warning("Vector Store Handler: No chunks provided to add.")
        return

    logger.info(f"--- Adding {len(rag_chunks)} Chunks to Vector Store (asyncpg) ---")
    db_config = load_db_config()
    conn: Optional[asyncpg.Connection] = None # Type hint for connection object
    inserted_count = 0
    skipped_count = 0

    # Pre-connection Check
    if not all([db_config["database"], db_config["user"], db_config["password"]]):
         error_msg = "Database connection details missing in .env (DB_NAME, DB_USER, DB_PASSWORD)."
         logger.critical(error_msg)
         raise ConnectionError(error_msg)

    try:
        # --- Connect using asyncpg ---
        logger.info(f"Connecting to PostgreSQL database '{db_config['database']}' on {db_config['host']}...")
        # Note: For production/frequent use, create_pool is generally preferred over connect
        conn = await asyncpg.connect(**db_config)
        logger.info("Database connection successful (asyncpg).")

        # Optional: Register pgvector type handler if needed (usually automatic with recent versions)
        # await register_vector(conn)

        # --- Prepare SQL Query ---
        # !!! IMPORTANT: ADJUST TABLE AND COLUMN NAMES BELOW !!!
        table_name = os.getenv("DB_VECTOR_TABLE", "your_vector_table") # ADJUST THIS
        chunk_id_col = "chunk_id"
        text_col = "text_content"
        metadata_col = "metadata" # JSONB
        vector_col = "embedding_vector" # VECTOR(dimension)

        # Use $1, $2, etc. placeholders for asyncpg parameters
        insert_query = f"""
            INSERT INTO {table_name} ({chunk_id_col}, {text_col}, {metadata_col}, {vector_col})
            VALUES ($1, $2, $3, $4)
            ON CONFLICT ({chunk_id_col}) DO UPDATE SET
                {text_col} = EXCLUDED.{text_col},
                {metadata_col} = EXCLUDED.{metadata_col},
                {vector_col} = EXCLUDED.{vector_col};
        """
        logger.info(f"Preparing to insert/update data into table '{table_name}'...")

        # --- Start Transaction ---
        async with conn.transaction():
            logger.debug("Transaction started.")
            # Consider using executemany for potential performance gain if inserting many rows
            # For upsert, executing one by one within transaction is often clearer
            for chunk in rag_chunks:
                chunk_id = chunk.get("chunk_id")
                text_content = chunk.get("text_content")
                metadata = chunk.get("metadata")
                embedding = chunk.get("embedding") # Should be List[float]

                # Validate required data
                if not chunk_id or not text_content or metadata is None or embedding is None:
                    logger.warning(f"Skipping chunk ID '{chunk_id}' due to missing data.")
                    skipped_count += 1
                    continue

                # --- Format Data ---
                try:
                    # 1. Metadata: asyncpg can often handle dicts directly for JSONB
                    #    If not, use json.dumps() as before. Let's try direct dict first.
                    metadata_to_insert = metadata # Pass dict directly

                    # 2. Embedding: asyncpg with pgvector *might* handle List[float] directly.
                    #    If it fails, convert to string '[f1,f2,...]' as fallback.
                    if isinstance(embedding, list) and all(isinstance(x, (int, float)) for x in embedding):
                        embedding_to_insert = embedding # Pass list directly
                    else:
                        logger.warning(f"Skipping chunk ID '{chunk_id}': Invalid embedding format.")
                        skipped_count += 1
                        continue
                except Exception as fmt_e:
                    logger.warning(f"Skipping chunk ID '{chunk_id}' due to data formatting error: {fmt_e}", exc_info=True)
                    skipped_count += 1
                    continue

                # --- Execute Query ---
                try:
                    logger.debug(f"Executing upsert for chunk ID: {chunk_id}")
                    # Pass parameters directly to execute
                    await conn.execute(insert_query, chunk_id, text_content, metadata_to_insert, embedding_to_insert)
                    inserted_count += 1
                except asyncpg.PostgresError as insert_error:
                    # Log specific Postgres errors
                    logger.error(f"Database error inserting/updating chunk ID {chunk_id}: {insert_error}", exc_info=True)
                    # Transaction will be rolled back automatically by 'async with' context manager
                    raise # Re-raise to stop processing this batch
                except Exception as exec_error:
                    logger.error(f"Unexpected error executing query for chunk ID {chunk_id}: {exec_error}", exc_info=True)
                    raise # Re-raise

            # Transaction commits automatically if 'async with' block exits without exception
            logger.info(f"Transaction committed. Attempted to add/update {inserted_count} chunks.")

        if skipped_count > 0:
             logger.warning(f"Skipped {skipped_count} chunks due to missing data or formatting errors.")

    except (asyncpg.PostgresError, OSError) as db_error: # Catch connection errors too
        logger.critical(f"Database connection or operation error: {db_error}", exc_info=True)
        # Wrap in ConnectionError for consistency? Or let specific error propagate?
        raise ConnectionError(f"Database connection or operation failed: {db_error}") from db_error
    except Exception as e:
        logger.critical(f"An unexpected error occurred interacting with the vector store: {e}", exc_info=True)
        raise # Re-raise other unexpected errors
    finally:
        # --- Close Connection ---
        if conn and not conn.is_closed():
            await conn.close()
            logger.info("Database connection closed (asyncpg).")


# Example usage block (for testing when script is run directly)
if __name__ == "__main__":
    # Configure logging for test run
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(name)s - %(message)s')
    logger.info("--- Running vector_store_handler.py (asyncpg) directly for testing ---")

    # --- !!! DANGER ZONE !!! ---
    logger.warning("This test block WILL attempt to connect to and write to the database.")
    logger.warning("Ensure you are using a TEST database and have created the table.")
    logger.warning("Verify table/column names and vector dimension in the script and .env.")

    # Sample chunks
    embedding_dim = 1536 # Match table definition
    sample_rag_chunks_with_embeddings = [
        {"chunk_id": "async_test_001", "text_content": "Async test chunk 1.", "metadata": {"s": "t1a"}, "embedding": [0.5] * embedding_dim},
        {"chunk_id": "async_test_002", "text_content": "Async test chunk 2.", "metadata": {"s": "t2a"}, "embedding": [0.6] * embedding_dim}
    ]
    logger.info(f"Sample Chunks to Add/Update: {len(sample_rag_chunks_with_embeddings)}")

    confirm = input("\nProceed with test database insertion/update? (yes/no): ")

    if confirm.lower() == 'yes':
        logger.info("Proceeding with test database operation...")
        try:
            # Run the async function using asyncio.run()
            asyncio.run(add_chunks_to_vector_store(sample_rag_chunks_with_embeddings))
            logger.info("Test database operation process completed (check database).")
        except ConnectionError as e:
            logger.error(f"Test failed due to connection error: {e}")
        except Exception as e:
            logger.error(f"An unexpected error occurred during testing: {e}", exc_info=True)
    else:
        logger.info("Test database operation cancelled by user.")

    logger.info("--- Vector Store Handler Test Complete ---")