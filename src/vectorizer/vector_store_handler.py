# -*- coding: utf-8 -*-
"""
Module responsible for interacting with the vector store (PostgreSQL + pgvector).

Handles database connection and provides functions to add or update
text chunks, their metadata, and their corresponding embeddings. Includes logging.
"""

import os
import sys
import asyncio
import json
import logging # Import logging
from typing import List, Dict, Any, Optional
# Database driver
import psycopg2
import psycopg2.extras
# Import dotenv
from dotenv import load_dotenv, find_dotenv

# Get a logger instance for this module
logger = logging.getLogger(__name__)

# --- Database Configuration ---
def load_db_config() -> Dict[str, Optional[str]]:
    """Loads database connection parameters from environment variables."""
    env_path = find_dotenv()
    if env_path:
        logger.info(f"Loading database config from: {env_path}")
        load_dotenv(dotenv_path=env_path, override=True)
    else:
        logger.warning(".env file not found for database config.")

    config = {
        "host": os.getenv("DB_HOST", "localhost"),
        "port": os.getenv("DB_PORT", "5432"),
        "database": os.getenv("DB_NAME"),
        "user": os.getenv("DB_USER"),
        "password": os.getenv("DB_PASSWORD"),
    }
    if not config["database"] or not config["user"] or not config["password"]:
        logger.warning("DB_NAME, DB_USER, or DB_PASSWORD not found in environment variables.")
    else:
        logger.info(f"DB Config Loaded: Host={config['host']}, Port={config['port']}, DB={config['database']}, User={config['user']}")
    return config

# --- Database Interaction (Async Placeholder with Sync Implementation) ---
async def add_chunks_to_vector_store(rag_chunks: List[Dict[str, Any]]):
    """
    Adds text chunks, metadata, and embeddings to the PostgreSQL vector store.

    Args:
        rag_chunks: List of chunk dictionaries with required keys.
    Raises:
        ConnectionError: If connection fails or credentials missing.
        ValueError: If a chunk is missing essential data.
        Exception: For errors during data insertion.
    """
    if not rag_chunks:
        logger.warning("Vector Store Handler: No chunks provided to add.")
        return

    logger.info(f"--- Adding {len(rag_chunks)} Chunks to Vector Store (PostgreSQL) ---")
    db_config = load_db_config()
    conn = None
    inserted_count = 0
    skipped_count = 0

    if not all([db_config["database"], db_config["user"], db_config["password"]]):
         error_msg = "Database connection details missing in .env (DB_NAME, DB_USER, DB_PASSWORD). Cannot connect."
         logger.critical(error_msg) # Use critical as this prevents operation
         raise ConnectionError(error_msg)

    try:
        logger.info(f"Connecting to PostgreSQL database '{db_config['database']}' on {db_config['host']}...")
        conn = psycopg2.connect(**db_config)
        conn.autocommit = False # Manage transactions
        cur = conn.cursor()
        logger.info("Database connection successful.")

        # !!! IMPORTANT: ADJUST TABLE AND COLUMN NAMES BELOW !!!
        table_name = "your_vector_table" # ADJUST THIS
        chunk_id_col = "chunk_id"         # ADJUST THIS
        text_col = "text_content"         # ADJUST THIS
        metadata_col = "metadata"         # ADJUST THIS (JSONB)
        vector_col = "embedding_vector"   # ADJUST THIS (VECTOR)

        insert_query = f"""
            INSERT INTO {table_name} ({chunk_id_col}, {text_col}, {metadata_col}, {vector_col})
            VALUES (%s, %s, %s, %s)
            ON CONFLICT ({chunk_id_col}) DO UPDATE SET
                {text_col} = EXCLUDED.{text_col},
                {metadata_col} = EXCLUDED.{metadata_col},
                {vector_col} = EXCLUDED.{vector_col};
        """

        logger.info(f"Preparing to insert/update data into table '{table_name}'...")
        for chunk in rag_chunks:
            chunk_id = chunk.get("chunk_id")
            text_content = chunk.get("text_content")
            metadata = chunk.get("metadata")
            embedding = chunk.get("embedding")

            if not chunk_id or not text_content or metadata is None or embedding is None:
                logger.warning(f"Skipping chunk ID '{chunk_id}' due to missing required data.")
                skipped_count += 1
                continue

            # --- Data Formatting ---
            try:
                metadata_json = json.dumps(metadata)
            except TypeError as e:
                logger.warning(f"Skipping chunk ID '{chunk_id}' due to non-serializable metadata: {e}")
                skipped_count += 1
                continue

            if isinstance(embedding, list):
                if not all(isinstance(x, (int, float)) for x in embedding):
                     logger.warning(f"Skipping chunk ID '{chunk_id}' due to non-numeric data in embedding list.")
                     skipped_count += 1
                     continue
                embedding_str = str(embedding).replace(" ", "")
            else:
                 logger.warning(f"Skipping chunk ID '{chunk_id}' because embedding is not a list.")
                 skipped_count += 1
                 continue

            # --- Execute Query ---
            try:
                logger.debug(f"Executing query for chunk ID: {chunk_id}")
                cur.execute(insert_query, (chunk_id, text_content, metadata_json, embedding_str))
                inserted_count += 1
            except psycopg2.Error as insert_error:
                 logger.error(f"Database error inserting/updating chunk ID {chunk_id}: {insert_error}", exc_info=True)
                 conn.rollback() # Rollback on error
                 raise Exception(f"Database error during insertion for chunk {chunk_id}") from insert_error
            except Exception as exec_error:
                 logger.error(f"Unexpected error executing query for chunk ID {chunk_id}: {exec_error}", exc_info=True)
                 conn.rollback()
                 raise

        # Commit the transaction if loop completed without raising errors
        conn.commit()
        logger.info(f"Transaction committed. Successfully added/updated {inserted_count} chunks.")
        if skipped_count > 0:
             logger.warning(f"Skipped {skipped_count} chunks due to missing data or formatting errors.")

    except psycopg2.Error as db_error:
        logger.critical(f"Database connection or setup error: {db_error}", exc_info=True)
        if conn: conn.rollback()
        raise ConnectionError(f"Database connection or operation failed: {db_error}") from db_error
    except Exception as e:
        logger.critical(f"An unexpected error occurred interacting with the vector store: {e}", exc_info=True)
        if conn: conn.rollback()
        raise
    finally:
        if conn:
            conn.close()
            logger.info("Database connection closed.")


# Example usage block (for testing when script is run directly)
if __name__ == "__main__":
    # Configure logging for test run
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(name)s - %(message)s')
    logger.info("--- Running vector_store_handler.py directly for testing ---")

    # --- !!! DANGER ZONE !!! ---
    logger.warning("This test block WILL attempt to connect to and write to the database.")
    logger.warning("Ensure you are using a TEST database and have created the table.")
    logger.warning("Verify table/column names and vector dimension in the script.")

    embedding_dim = 1536
    sample_rag_chunks_with_embeddings = [
        {"chunk_id": "test_chunk_001", "text_content": "Test chunk 1.", "metadata": {"s": "t1"}, "embedding": [0.1] * embedding_dim},
        {"chunk_id": "test_chunk_002", "text_content": "Test chunk 2.", "metadata": {"s": "t2"}, "embedding": [0.2] * embedding_dim}
    ]
    logger.info(f"Sample Chunks to Add: {len(sample_rag_chunks_with_embeddings)}")

    confirm = input("\nProceed with test database insertion? (yes/no): ")

    if confirm.lower() == 'yes':
        logger.info("Proceeding with test insertion...")
        try:
            asyncio.run(add_chunks_to_vector_store(sample_rag_chunks_with_embeddings))
            logger.info("Test insertion process completed (check database for results/errors).")
        except ConnectionError as e:
            logger.error(f"Test failed due to connection error: {e}")
        except Exception as e:
            logger.error(f"An unexpected error occurred during testing: {e}", exc_info=True)
    else:
        logger.info("Test insertion cancelled by user.")

    logger.info("--- Vector Store Handler Test Complete ---")