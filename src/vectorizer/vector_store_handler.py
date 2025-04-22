# -*- coding: utf-8 -*-
"""
Module responsible for interacting with the vector store (PostgreSQL + pgvector).

Handles database connection and provides functions to add or update
text chunks, their metadata, and their corresponding embeddings in the
appropriate PostgreSQL table. Designed with async operations in mind
to align with the modular-dashboard backend stack (SQLAlchemy 2+ Asyncio, asyncpg).
"""

import os
import sys
import asyncio # For async operations
from typing import List, Dict, Any, Optional
# Database driver - ensure psycopg2-binary is installed
import psycopg2
import psycopg2.extras # For dict cursor or other helpers
# Import asyncpg if planning direct async operations later
# import asyncpg

# Import dotenv to load database credentials
from dotenv import load_dotenv, find_dotenv

# --- Database Configuration ---
# Load database connection details from .env file
# Recommended .env variables: DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD
def load_db_config() -> Dict[str, Optional[str]]:
    """Loads database connection parameters from environment variables."""
    env_path = find_dotenv()
    if env_path:
        print(f"Loading database config from: {env_path}")
        load_dotenv(dotenv_path=env_path, override=True)
    else:
        print("Warning: .env file not found for database config.", file=sys.stderr)

    config = {
        "host": os.getenv("DB_HOST", "localhost"), # Default to localhost
        "port": os.getenv("DB_PORT", "5432"),     # Default PostgreSQL port
        "database": os.getenv("DB_NAME"),
        "user": os.getenv("DB_USER"),
        "password": os.getenv("DB_PASSWORD"),
    }
    # Check if essential variables are set
    if not config["database"] or not config["user"] or not config["password"]:
        print("Warning: DB_NAME, DB_USER, or DB_PASSWORD not found in environment variables.", file=sys.stderr)
        # Decide if this should be a fatal error depending on usage context
    return config

# --- Database Interaction (Async Placeholder) ---
# Note: The actual implementation will likely use SQLAlchemy's async features
# or asyncpg directly for better integration with FastAPI backend.
# This placeholder uses standard psycopg2 synchronously for initial structure.
# A proper async implementation is more complex.

async def add_chunks_to_vector_store(rag_chunks: List[Dict[str, Any]]):
    """
    Adds text chunks, metadata, and embeddings to the PostgreSQL vector store.

    Connects to the database specified in .env and inserts the data into
    the appropriate table (structure needs to be defined/known).

    Args:
        rag_chunks: A list of dictionaries, each representing a chunk with
                    'chunk_id', 'text_content', 'metadata', and 'embedding' keys.

    Raises:
        ConnectionError: If connection to the database fails.
        Exception: For errors during data insertion.
    """
    if not rag_chunks:
        print("  Vector Store Handler: No chunks provided to add.")
        return

    print(f"\n--- Adding {len(rag_chunks)} Chunks to Vector Store (PostgreSQL) ---")
    db_config = load_db_config()
    conn = None
    # Placeholder for successful insertions count
    inserted_count = 0

    # Basic check if essential config is missing
    if not all([db_config["database"], db_config["user"], db_config["password"]]):
         print("  Error: Database connection details missing in .env. Cannot connect.", file=sys.stderr)
         # Depending on workflow, might raise an error or just return
         raise ConnectionError("Missing database credentials in environment variables.")

    try:
        # --- Connect to PostgreSQL (Synchronous Example) ---
        # TODO: Replace with async connection pool (e.g., using asyncpg or SQLAlchemy async)
        print(f"  Connecting to PostgreSQL database '{db_config['database']}' on {db_config['host']}...")
        conn = psycopg2.connect(
            host=db_config["host"],
            port=db_config["port"],
            database=db_config["database"],
            user=db_config["user"],
            password=db_config["password"]
        )
        conn.autocommit = False # Use transactions
        cur = conn.cursor()
        print("  Database connection successful.")

        # --- Prepare and Execute INSERT Statements ---
        # IMPORTANT: Replace 'your_vector_table' with the actual table name
        #            and column names used in the modular-dashboard database.
        #            Ensure the table exists with a 'vector' column of type 'vector(DIMENSION)'
        #            where DIMENSION matches the embedding dimension (e.g., 1536 for OpenAI small).
        #            Metadata should likely be stored in a JSONB column or separate columns.
        insert_query = """
            INSERT INTO your_vector_table (chunk_id, text_content, metadata, embedding_vector)
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (chunk_id) DO UPDATE SET -- Example: Update if chunk_id exists
                text_content = EXCLUDED.text_content,
                metadata = EXCLUDED.metadata,
                embedding_vector = EXCLUDED.embedding_vector;
        """
        # Note: Storing vectors requires the vector to be formatted as a string '[1.2, 3.4, ...]'
        # psycopg2 might handle list-to-string conversion automatically for vector type,
        # but verify this. If not, convert embedding list to string format.

        for chunk in rag_chunks:
            chunk_id = chunk.get("chunk_id")
            text_content = chunk.get("text_content")
            metadata = chunk.get("metadata")
            embedding = chunk.get("embedding")

            if not all([chunk_id, text_content, metadata, embedding]):
                print(f"  Warning: Skipping chunk due to missing data (ID: {chunk_id}).", file=sys.stderr)
                continue

            # Convert metadata dict to JSON string for JSONB column
            metadata_json = json.dumps(metadata)
            # Convert embedding list to string format required by pgvector (e.g., '[0.1, 0.2, ...]')
            # Note: Check if psycopg2 handles this conversion; if not, implement manually.
            embedding_str = str(embedding) # Basic conversion, might need refinement

            try:
                # Execute the insert/update query
                cur.execute(insert_query, (chunk_id, text_content, metadata_json, embedding_str))
                inserted_count += 1
            except Exception as insert_error:
                 print(f"  Error inserting chunk ID {chunk_id}: {insert_error}", file=sys.stderr)
                 # Decide whether to rollback or continue with other chunks
                 conn.rollback() # Rollback this chunk's attempt
                 # Optionally break or continue processing other chunks

        # Commit the transaction if all insertions were successful (or handled)
        conn.commit()
        print(f"  Successfully added/updated {inserted_count} chunks in the vector store.")

    except psycopg2.Error as db_error:
        print(f"Database error: {db_error}", file=sys.stderr)
        if conn:
            conn.rollback() # Rollback any partial transaction
        # Re-raise as a ConnectionError or specific DB error
        raise ConnectionError(f"Database connection or operation failed: {db_error}") from db_error
    except Exception as e:
        print(f"An unexpected error occurred interacting with the vector store: {e}", file=sys.stderr)
        if conn:
            conn.rollback()
        raise # Re-raise other unexpected errors
    finally:
        # Ensure the database connection is closed
        if conn:
            conn.close()
            print("  Database connection closed.")


# Example usage block (for testing when script is run directly)
if __name__ == "__main__":
    print("\n--- Running vector_store_handler.py directly for testing ---")
    # Requires .env file with DB credentials (DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD)
    # Assumes a PostgreSQL database with pgvector extension enabled and a table exists.

    # --- !!! DANGER ZONE: MODIFYING DATABASE !!! ---
    # This test block WILL attempt to connect to and modify the database specified in .env.
    # 1. **DO NOT run this against a production database.**
    # 2. **Ensure you have a test database configured.**
    # 3. **Verify the table name and structure in the insert_query above.**
    # 4. **Create the table manually first if it doesn't exist.** Example SQL:
    #    CREATE EXTENSION IF NOT EXISTS vector; -- Enable pgvector
    #    CREATE TABLE your_vector_table (
    #        chunk_id TEXT PRIMARY KEY,
    #        text_content TEXT,
    #        metadata JSONB,
    #        embedding_vector VECTOR(1536) -- Adjust dimension (1536 for openai-3-small)
    #    );
    #    -- Optional: Create an index for faster similarity search
    #    CREATE INDEX ON your_vector_table USING hnsw (embedding_vector vector_l2_ops); -- Or ivfflat

    # Sample chunks with embeddings (replace with actual embeddings if needed)
    # Dimension must match the table definition (e.g., 1536)
    embedding_dim = 1536 # Example dimension matching text-embedding-3-small default
    sample_rag_chunks_with_embeddings = [
        {
            "chunk_id": "test_chunk_001",
            "text_content": "Este é um chunk de teste para o banco de dados vetorial.",
            "metadata": {"source": "test_script", "page": 1},
            "embedding": [0.1] * embedding_dim # Dummy embedding
        },
        {
            "chunk_id": "test_chunk_002",
            "text_content": "Outro chunk de teste com informações diferentes.",
            "metadata": {"source": "test_script", "page": 2, "author": "tester"},
            "embedding": [0.2] * embedding_dim # Dummy embedding
        }
    ]

    print("\nSample Chunks to Add:")
    # print(json.dumps(sample_rag_chunks_with_embeddings, indent=2)) # Can be long

    # --- Confirmation Prompt ---
    print("\nWARNING: This test will attempt to write to the database configured in .env.")
    confirm = input("Proceed with test database insertion? (yes/no): ")

    if confirm.lower() == 'yes':
        try:
            # Use asyncio.run() to execute the async function from sync context
            # Note: This is a simplified way for testing; integration with an async
            # application (like FastAPI) would manage the event loop differently.
            asyncio.run(add_chunks_to_vector_store(sample_rag_chunks_with_embeddings))
            print("\nTest insertion process completed.")
        except ConnectionError as e:
            print(f"\nTest failed due to connection error: {e}")
        except Exception as e:
            print(f"\nAn unexpected error occurred during testing: {e}")
    else:
        print("\nTest insertion cancelled by user.")

    print("\n--- Vector Store Handler Test Complete ---")