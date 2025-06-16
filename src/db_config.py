import asyncpg
import os
import logging

logger = logging.getLogger(__name__)

# Database connection parameters from environment variables with defaults
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "postgres")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "transcritor_pdf_db") # Changed default for clarity

DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

# Placeholder for embedding dimensions - this might come from a model config later
# For now, common dimensions are 384 (e.g., all-MiniLM-L6-v2), 768 (e.g., BERT base), 1536 (OpenAI Ada-002)
EMBEDDING_DIMENSIONS = int(os.getenv("EMBEDDING_DIMENSIONS", "1536"))

# Global variable for the connection pool
# Explicitly type hint that it can be None initially
db_pool: asyncpg.Pool | None = None

async def connect_to_db():
    """
    Establishes a connection pool to the PostgreSQL database.
    The pool is stored in the global `db_pool` variable.
    """
    global db_pool
    if db_pool is not None:
        logger.info("Database connection pool already exists.")
        return

    logger.info(f"Attempting to connect to database: {DB_HOST}:{DB_PORT}/{DB_NAME} as user {DB_USER}")
    try:
        pool = await asyncpg.create_pool(
            dsn=DATABASE_URL,
            min_size=int(os.getenv("DB_POOL_MIN_SIZE", "1")),
            max_size=int(os.getenv("DB_POOL_MAX_SIZE", "10")),
            # Add other pool settings if needed, e.g., timeouts
            # command_timeout=60,  # Example: Default command timeout for connections from this pool
        )
        if pool:
            db_pool = pool
            logger.info("Successfully connected to the database and created connection pool.")
            # Optionally, test the connection with a simple query
            async with db_pool.acquire() as conn:
                await conn.fetchval("SELECT 1")
            logger.info("Database connection pool test query successful.")
        else:
            logger.error("asyncpg.create_pool returned None. Pool creation failed.")
            # This case should ideally not happen if create_pool doesn't raise an exception
            # but it's good to be aware of.

    except asyncpg.exceptions.PostgresError as pe: # More specific asyncpg errors
        logger.error(f"PostgreSQL error while connecting to the database: {pe}")
        # Depending on the app's needs, you might want to sys.exit() or raise
    except Exception as e:
        logger.error(f"Failed to connect to the database and create pool: {e}", exc_info=True)
        # Optionally re-raise or handle as appropriate for startup (e.g., sys.exit for critical failure)
        # raise # Re-raise if you want the application to fail on startup if DB connection fails

async def close_db_connection():
    """
    Closes the database connection pool if it exists.
    """
    global db_pool
    if db_pool:
        logger.info("Closing database connection pool...")
        try:
            await db_pool.close()
            db_pool = None # Ensure it's reset
            logger.info("Database connection pool closed successfully.")
        except Exception as e:
            logger.error(f"Error while closing database connection pool: {e}", exc_info=True)
    else:
        logger.info("No active database connection pool to close.")

# Example of how to use (typically called at app startup/shutdown):
# async def main_app_lifecycle():
#     await connect_to_db()
#     # ... your application runs ...
#     if db_pool: # Check if pool was successfully created
#         # Example usage
#         async with db_pool.acquire() as conn:
#             val = await conn.fetchval("SELECT $1::TEXT", "Hello DB")
#             print(f"Test query result: {val}")
#     await close_db_connection()

# if __name__ == "__main__":
#     logging.basicConfig(level=logging.INFO) # Ensure logger is configured for standalone run
#     asyncio.run(main_app_lifecycle())
