# asyncpg Summary Reference

This document summarizes key concepts, common operations, and usage patterns for `asyncpg`, a database interface library for PostgreSQL and Python/asyncio.

**Source Documentation:**
*   Main: [https://magicstack.github.io/asyncpg/current/](https://magicstack.github.io/asyncpg/current/)
*   Usage: [https://magicstack.github.io/asyncpg/current/usage.html](https://magicstack.github.io/asyncpg/current/usage.html)
*   API Reference: [https://magicstack.github.io/asyncpg/current/api/index.html](https://magicstack.github.io/asyncpg/current/api/index.html)

## Key Concepts

*   **Asynchronous:** Designed for use with `asyncio`.
*   **PostgreSQL Specific:** Optimized for PostgreSQL, using its binary protocol.
*   **Type Conversion:** Automatic conversion between PostgreSQL and Python types.
*   **Connection Pooling:** Built-in support for managing multiple database connections.
*   **Prepared Statements:** Efficiently execute queries that are run multiple times.

## Establishing a Connection

Connections are established using `asyncpg.connect()`.

**Connection Parameters:**
Can be provided as a DSN string or keyword arguments. Keywords override DSN values. Environment variables (e.g., `PGHOST`, `PGUSER`, `PGPASSWORD`, `PGDATABASE`) are also used if parameters are not explicitly provided.

*   **DSN (Data Source Name) string:**
    ```
    postgres://user:password@host:port/database?option=value
    ```
    Example: `conn = await asyncpg.connect('postgresql://postgres:secret@localhost:5432/mydatabase')`

*   **Keyword Arguments:**
    ```python
    import asyncpg
    import asyncio

    async def main():
        conn = await asyncpg.connect(
            user='your_user',
            password='your_password',
            database='your_database',
            host='your_host', # Defaults to localhost or Unix socket
            port=5432      # Defaults to 5432
        )
        # ... use connection ...
        await conn.close()

    # asyncio.run(main())
    ```

**Closing Connection:**
Always ensure connections are closed when done.
```python
await conn.close()
```

## Executing Queries

`asyncpg` uses `$n` for query argument placeholders (e.g., `$1`, `$2`).

1.  **`conn.execute(query, *args, timeout=None) -> str`**:
    *   Executes an SQL command (or multiple commands if no arguments are provided).
    *   Returns the status of the last SQL command (e.g., "INSERT 0 1", "CREATE TABLE").
    *   Suitable for DDL (Data Definition Language) like `CREATE TABLE`, `CREATE EXTENSION`, and DML (Data Manipulation Language) like `INSERT`, `UPDATE`, `DELETE` where you don't need to fetch results.

    ```python
    # DDL Example
    await conn.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id serial PRIMARY KEY,
            name text,
            email text UNIQUE
        );
    ''')
    await conn.execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp";') # Example for extensions

    # DML Example
    status = await conn.execute(
        "INSERT INTO users (name, email) VALUES ($1, $2)",
        'John Doe', 'john.doe@example.com'
    )
    print(status) # e.g., "INSERT 0 1"
    ```

2.  **`conn.fetch(query, *args, timeout=None) -> list[Record]`**:
    *   Executes a query and returns all rows as a list of `asyncpg.Record` objects.
    *   `asyncpg.Record` objects allow accessing columns by index or name.

    ```python
    rows = await conn.fetch("SELECT id, name, email FROM users WHERE name LIKE $1", 'John%')
    for row in rows:
        print(f"ID: {row['id']}, Name: {row['name']}, Email: {row['email']}")
        # Or by index: print(row[0], row[1], row[2])
    ```

3.  **`conn.fetchrow(query, *args, timeout=None) -> Record | None`**:
    *   Executes a query and returns the first row as an `asyncpg.Record` object, or `None` if no rows are found.

    ```python
    row = await conn.fetchrow("SELECT * FROM users WHERE id = $1", 1)
    if row:
        print(f"User found: {row['name']}")
    else:
        print("User not found.")
    ```

4.  **`conn.fetchval(query, *args, column=0, timeout=None) -> Any | None`**:
    *   Executes a query and returns a single value from the first row.
    *   `column`: Specifies the 0-based index of the column to return. Defaults to the first column (0).
    *   Returns `None` if no rows are found.

    ```python
    user_count = await conn.fetchval("SELECT COUNT(*) FROM users")
    print(f"Total users: {user_count}")

    user_email = await conn.fetchval("SELECT email FROM users WHERE id = $1", 1)
    if user_email:
        print(f"User email: {user_email}")
    ```

5.  **`conn.executemany(command, args_list, timeout=None)`**:
    *   Executes a command for each sequence of arguments in `args_list`.
    *   Useful for bulk inserts/updates. Does not return results.
    *   Atomic by default (all succeed or none).

    ```python
    users_to_add = [
        ('Alice', 'alice@example.com'),
        ('Bob', 'bob@example.com')
    ]
    await conn.executemany(
        "INSERT INTO users (name, email) VALUES ($1, $2)",
        users_to_add
    )
    ```

## Prepared Statements

Prepared statements optimize queries executed multiple times.

```python
stmt = await conn.prepare("SELECT name FROM users WHERE email LIKE $1")
# stmt is an asyncpg.PreparedStatement object

# Execute the prepared statement
user_name_1 = await stmt.fetchval('john%')
user_name_2 = await stmt.fetchval('jane%')

# PreparedStatement methods: .fetch(), .fetchrow(), .fetchval(), .cursor(), .executemany()
```
`asyncpg` also has an automatic LRU cache for statements used in `fetch()`, `fetchrow()`, `fetchval()`.

## Transactions

Use `conn.transaction()` for atomic operations.

```python
async with conn.transaction():
    # All operations here are part of a single transaction
    await conn.execute("INSERT INTO users (name, email) VALUES ($1, $2)", 'Temp User', 'temp@example.com')
    await conn.execute("DELETE FROM logs WHERE user_email = $1", 'temp@example.com')
# Transaction is automatically committed on successful exit of 'async with' block,
# or rolled back if an exception occurs.
```

Manual transaction control:
```python
tr = conn.transaction()
await tr.start()
try:
    # ... operations ...
    await tr.commit()
except:
    await tr.rollback()
    raise
```

## Connection Pools

Recommended for server applications to manage connections efficiently.

1.  **Creating a Pool (`asyncpg.create_pool()`):**
    ```python
    pool = await asyncpg.create_pool(
        user='your_user', password='your_password', database='your_database', host='your_host',
        min_size=1,  # Minimum number of connections in the pool
        max_size=10  # Maximum number of connections in the pool
    )
    ```
    Other parameters include `max_queries` (queries before connection reset), `max_inactive_connection_lifetime`, `setup` (coroutine to run on new connections), `init` (coroutine for initial setup).

2.  **Acquiring a Connection (`pool.acquire()`):**
    Connections are acquired from the pool and should be released back.
    ```python
    async with pool.acquire() as connection:
        # Use 'connection' like a regular asyncpg.Connection object
        result = await connection.fetchval('SELECT 2 ^ $1', 10)
        print(result)
    # Connection is automatically released back to the pool here.
    ```
    Or manually:
    ```python
    conn = await pool.acquire()
    try:
        # ... use conn ...
    finally:
        await pool.release(conn)
    ```

3.  **Executing Queries Directly with Pool:**
    The `Pool` object also provides `execute()`, `fetch()`, `fetchrow()`, `fetchval()` methods that implicitly acquire a connection, run the query, and release the connection.
    ```python
    result = await pool.fetchval('SELECT 2 ^ $1', 10) # Simpler for single operations
    ```

4.  **Closing a Pool:**
    ```python
    await pool.close() # Gracefully close all connections
    # pool.terminate() # Forcefully terminate all connections
    ```

## Error Handling

`asyncpg` raises exceptions for various database errors. Common ones include:
*   `asyncpg.exceptions.PostgresError`: Base class for most PostgreSQL errors.
*   `asyncpg.exceptions.PostgresSyntaxError`: For SQL syntax errors.
*   `asyncpg.exceptions.UniqueViolationError`: For unique constraint violations.
*   `asyncpg.exceptions.ForeignKeyViolationError`: For foreign key violations.
*   `asyncpg.exceptions.ConnectionDoesNotExistError`: If a connection is unexpectedly closed.
*   `TimeoutError` (from `asyncio`): If query or connection timeouts are exceeded.

Catch exceptions using standard `try...except` blocks:
```python
try:
    await conn.execute("INSERT INTO users (name, email) VALUES ($1, $1)", "Duplicate") # Will fail if email is unique
except asyncpg.exceptions.UniqueViolationError as uve:
    print(f"Could not insert: {uve}")
except asyncpg.exceptions.PostgresError as e:
    print(f"A PostgreSQL error occurred: {e}")
except Exception as e:
    print(f"An unexpected error occurred: {e}")
```

## Best Practices for FastAPI (Inferred)

*   **Connection Pool Lifecycle:**
    *   Create the connection pool when the FastAPI application starts up (e.g., using an `on_event("startup")` handler).
    *   Close the connection pool when the FastAPI application shuts down (e.g., using an `on_event("shutdown")` handler).
    ```python
    # In your FastAPI main.py or a db.py module
    # app = FastAPI()
    # app.state.pool = None # For storing the pool

    # @app.on_event("startup")
    # async def startup_db_client():
    #     app.state.pool = await asyncpg.create_pool(user="...", database="...")

    # @app.on_event("shutdown")
    # async def shutdown_db_client():
    #     if app.state.pool:
    #         await app.state.pool.close()
    ```

*   **Managing Connections per Request:**
    *   For each request that needs database access, acquire a connection from the pool.
    *   Ensure the connection is released after the request is handled, even if errors occur. The `async with pool.acquire() as connection:` pattern is best for this.

    ```python
    # Example in an endpoint
    # @app.get("/users/{user_id}")
    # async def get_user(request: Request, user_id: int):
    #     pool = request.app.state.pool
    #     async with pool.acquire() as conn:
    #         user_record = await conn.fetchrow("SELECT * FROM users WHERE id = $1", user_id)
    #         if not user_record:
    #             raise HTTPException(status_code=404, detail="User not found")
    #         return user_record
    ```

This summary provides a good foundation for using `asyncpg`. For more advanced features or specific error codes, refer to the official API documentation.
