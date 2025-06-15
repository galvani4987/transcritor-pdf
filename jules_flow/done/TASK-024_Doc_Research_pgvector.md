---
id: TASK-024
title: "Doc Research: pgvector (Vector Storage with PostgreSQL)"
epic: "Documentation"
status: done
priority: medium
dependencies: []
assignee: Jules
---

### Descrição

Research official documentation for pgvector. Identify key concepts, setup (including PostgreSQL extension), usage patterns (creating vector columns, indexing, querying), and best practices relevant to its planned use in the 'transcritor-pdf' project for storing and querying PDF embeddings. Create a summary reference file named `docs/reference/pgvector_summary.txt`.

### Critérios de Aceitação

- [ ] Official documentation website(s) for pgvector (and relevant PostgreSQL aspects) identified and accessed.
- [ ] Key information relevant to the project (setup, `CREATE EXTENSION vector;`, table creation with vector types, indexing strategies, similarity search queries, integration with `asyncpg`) reviewed.
- [ ] Summary reference file `docs/reference/pgvector_summary.txt` created with key findings, relevant links, and code snippets if applicable.

### Arquivos Relevantes

* `ROADMAP.md`
* `requirements.txt`
* `src/vector_store_handler.py`
* `docs/reference/pgvector_summary.txt`

### Relatório de Execução

Successfully researched pgvector.
- Accessed the official pgvector documentation on GitHub (https://github.com/pgvector/pgvector).
- Extracted key information including:
  - Installation and enabling the `vector` extension.
  - The `vector(dimensions)` data type.
  - SQL examples for table creation with vector columns.
  - HNSW and IVFFlat index types and their creation.
  - SQL examples for inserting vector data and performing similarity searches (L2, inner product, cosine distance).
  - Notes on indexing and performance.
- Created the summary file `docs/reference/pgvector_summary.txt` with this information and a link to the source.
