---
id: TASK-033
title: "DB: Resolve Schema Mismatch"
epic: "System Consistency & Correction"
status: done
priority: high
dependencies: []
assignee: Jules
---

### Descrição

Database schema for 'documents' table differs between creation in `src/main.py` and usage in `src/vectorizer/vector_store_handler.py`. Issues include table name (documents vs. your_vector_table/DB_VECTOR_TABLE), vector column name (embedding vs. embedding_vector), and primary/conflict key (id/UNIQUE(filename,page_number) vs. chunk_id).

### Critérios de Aceitação

- [ ] `src/vectorizer/vector_store_handler.py` uses the table name 'documents'.
- [ ] `src/vectorizer/vector_store_handler.py` uses 'embedding' as the vector column name in SQL.
- [ ] `src/main.py` schema for 'documents' table includes `chunk_id TEXT PRIMARY KEY` (replacing `id SERIAL PRIMARY KEY`).
- [ ] `src/vectorizer/vector_store_handler.py` uses `ON CONFLICT (chunk_id) DO UPDATE` correctly with the new schema.
- [ ] Decision on `UNIQUE(filename, page_number)` constraint considered and adjusted if necessary with `chunk_id`.

### Arquivos Relevantes

* `src/main.py`
* `src/vectorizer/vector_store_handler.py`

### Relatório de Execução

Subtask completed successfully.
- Modified `src/main.py` (`startup_db_event`):
    - Changed `CREATE TABLE IF NOT EXISTS documents` schema.
    - Primary key is now `chunk_id TEXT PRIMARY KEY` (removed `id SERIAL PRIMARY KEY`).
    - Vector column is named `embedding`.
    - Removed `UNIQUE(filename, page_number)` constraint.
- Modified `src/vectorizer/vector_store_handler.py`:
    - Changed `table_name` to `"documents"`.
    - Updated `insert_query` to use `embedding` as vector column and `ON CONFLICT (chunk_id)`.
The changes align table name, primary key, and embedding column name.
