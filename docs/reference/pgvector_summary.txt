# pgvector Summary Reference

This document summarizes key concepts, SQL examples, and usage notes for the pgvector PostgreSQL extension, based on its official GitHub documentation.

**Source Documentation:** [https://github.com/pgvector/pgvector](https://github.com/pgvector/pgvector) (Primarily from the README)

## Key Concepts

*   **Vector Similarity Search:** pgvector allows storing and searching vector embeddings in PostgreSQL.
*   **Data Types:** Supports `vector`, `halfvec` (half-precision), `bit` (binary), and `sparsevec`.
*   **Distance Metrics:** Supports L2 distance, inner product, cosine distance, L1 distance, Hamming distance, and Jaccard distance.
*   **Indexing:** Offers exact nearest neighbor search by default and approximate nearest neighbor (ANN) search using IVFFlat or HNSW indexes for performance.
*   **ACID Compliance:** Benefits from PostgreSQL's ACID properties, point-in-time recovery, JOINs, etc.

## Installation and Setup

1.  **Install the extension:**
    *   Various methods exist (compiling from source, Docker, Homebrew, PGXN, APT, Yum, etc.). Refer to the "Installation" section of the pgvector README for specifics.
    *   Example for compiling (Postgres 13+):
        ```bash
        cd /tmp
        git clone --branch v0.8.0 https://github.com/pgvector/pgvector.git # Check for latest version
        cd pgvector
        make
        sudo make install
        ```
    *   Ensure PostgreSQL development files are installed (e.g., `postgresql-server-dev-17` on Debian/Ubuntu).

2.  **Enable the extension in PostgreSQL:**
    *   Connect to your PostgreSQL database and run this command once per database:
        ```sql
        CREATE EXTENSION vector;
        ```

## Vector Data Type

*   The primary data type is `vector(dimensions)`, where `dimensions` is the number of dimensions in your vector.
    *   Example: `vector(3)` for a 3-dimensional vector.
    *   Example: `vector(1536)` for OpenAI Ada-002 embeddings.
*   Vectors can have up to 16,000 dimensions.
*   Each element is a single-precision floating-point number.
*   `halfvec(dimensions)`: For half-precision floating-point numbers (smaller storage, up to 16,000 dimensions).
*   `bit(dimensions)`: For binary vectors (e.g., from image hashing, up to 64,000 dimensions).
*   `sparsevec(dimensions)`: For sparse vectors (stores non-zero elements and their indices, up to 16,000 non-zero elements).

## Table Creation

*   Create a new table with a vector column:
    ```sql
    CREATE TABLE items (
        id bigserial PRIMARY KEY,
        embedding vector(3) -- Example for 3 dimensions
    );
    ```
*   Add a vector column to an existing table:
    ```sql
    ALTER TABLE items ADD COLUMN embedding vector(3);
    ```

## Inserting Vector Data

*   Insert vectors as string representations:
    ```sql
    INSERT INTO items (embedding) VALUES ('[1,2,3]'), ('[4,5,6]');
    ```
*   For bulk loading, use `COPY`:
    ```sql
    COPY items (embedding) FROM STDIN WITH (FORMAT BINARY);
    -- Followed by binary data stream
    ```
*   Upsert vectors:
    ```sql
    INSERT INTO items (id, embedding) VALUES (1, '[1,2,3]'), (2, '[4,5,6]')
        ON CONFLICT (id) DO UPDATE SET embedding = EXCLUDED.embedding;
    ```

## Querying and Similarity Search

pgvector supports several distance operators:

*   `<->`: L2 distance (Euclidean distance)
*   `<#>`: Negative Inner Product (use `* -1` for actual inner product; Postgres only supports ASC order index scans)
*   `<=>`: Cosine Distance (use `1 - (embedding <=> query_vector)` for cosine similarity)
*   `<+>`: L1 distance (Manhattan distance)
*   `<~>`: Hamming distance (for `bit` vectors)
*   `<%"`: Jaccard distance (for `bit` vectors)

**Examples:**

1.  **Get nearest neighbors by L2 distance:**
    ```sql
    SELECT * FROM items ORDER BY embedding <-> '[3,1,2]' LIMIT 5;
    ```

2.  **Get nearest neighbors by Inner Product (higher is more similar):**
    ```sql
    -- <#> returns negative inner product, so ORDER BY ASC means most similar
    SELECT *, (embedding <#> '[3,1,2]') * -1 AS inner_product FROM items ORDER BY embedding <#> '[3,1,2]' LIMIT 5;
    ```

3.  **Get nearest neighbors by Cosine Similarity (higher is more similar):**
    ```sql
    -- <=> is cosine distance (0 is identical, 2 is opposite)
    -- To get cosine similarity (1 is identical, -1 is opposite), use 1 - distance
    SELECT *, 1 - (embedding <=> '[3,1,2]') AS cosine_similarity FROM items ORDER BY embedding <=> '[3,1,2]' LIMIT 5;
    ```

4.  **Get rows within a certain L2 distance:**
    ```sql
    SELECT * FROM items WHERE embedding <-> '[3,1,2]' < 5;
    -- Note: Combine with ORDER BY and LIMIT to leverage indexes effectively.
    ```

5.  **Get distance value:**
    ```sql
    SELECT embedding <-> '[3,1,2]' AS distance FROM items;
    ```

## Indexing Vector Columns

By default, pgvector performs exact nearest neighbor search. For larger datasets, approximate nearest neighbor (ANN) search using indexes is recommended for performance.

**Supported Index Types:**

*   **HNSW (Hierarchical Navigable Small World):**
    *   Better query performance (speed-recall tradeoff) than IVFFlat.
    *   Slower build times and uses more memory.
    *   Does not require training data before index creation.
    *   Create an index for each distance function you plan to use.
        *   L2 distance: `CREATE INDEX ON items USING hnsw (embedding vector_l2_ops);`
        *   Inner product: `CREATE INDEX ON items USING hnsw (embedding vector_ip_ops);`
        *   Cosine distance: `CREATE INDEX ON items USING hnsw (embedding vector_cosine_ops);`
        *   L1 distance: `CREATE INDEX ON items USING hnsw (embedding vector_l1_ops);`
    *   HNSW options: `m` (connections per layer, default 16), `ef_construction` (candidate list size for graph construction, default 64).
        ```sql
        CREATE INDEX ON items USING hnsw (embedding vector_l2_ops) WITH (m = 16, ef_construction = 64);
        ```
    *   Query-time option: `hnsw.ef_search` (candidate list size for search, default 40).
        ```sql
        SET hnsw.ef_search = 100;
        ```

*   **IVFFlat (Inverted File with Flat lists):**
    *   Faster build times and less memory usage than HNSW.
    *   Lower query performance (speed-recall tradeoff).
    *   Requires some data in the table before index creation for training.
    *   Key parameters:
        *   `lists`: Number of inverted lists. Start with `rows / 1000` (up to 1M rows) or `sqrt(rows)` (over 1M rows).
        *   `probes` (query-time): Number of lists to search. Start with `sqrt(lists)`.
    *   Create an index for each distance function:
        *   L2 distance: `CREATE INDEX ON items USING ivfflat (embedding vector_l2_ops) WITH (lists = 100);`
        *   Inner product: `CREATE INDEX ON items USING ivfflat (embedding vector_ip_ops) WITH (lists = 100);`
        *   Cosine distance: `CREATE INDEX ON items USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);`
    *   Query-time option: `ivfflat.probes`.
        ```sql
        SET ivfflat.probes = 10;
        ```

**General Indexing Notes:**
*   It's generally faster to create an index after loading initial data.
*   For production, consider `CREATE INDEX CONCURRENTLY` to avoid blocking writes.
*   Use `EXPLAIN ANALYZE` to check if queries are using the index.

## Other Considerations

*   **Filtering with Indexes:** For queries with `WHERE` clauses, create standard PostgreSQL indexes on the filter columns. For ANN indexes, filtering is typically applied *after* the approximate search. Iterative index scans (pgvector 0.8.0+) can improve this.
*   **Half-Precision (`halfvec`):** Can be used for smaller index sizes. Cast to `halfvec` during indexing and querying if the stored type is `vector`.
*   **Binary Quantization:** Can further reduce index size by converting vectors to binary representations.
*   **Performance Tuning:** Standard PostgreSQL tuning (e.g., `shared_buffers`, `maintenance_work_mem`) applies. `maintenance_work_mem` is particularly important for HNSW index build times.
*   **Upgrading:** `ALTER EXTENSION vector UPDATE;` after installing a new version of the pgvector binaries.

This summary provides a starting point. For detailed information, always refer to the [official pgvector documentation](https://github.com/pgvector/pgvector).
