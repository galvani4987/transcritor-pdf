---
id: TASK-013
title: "F7: Implementar Gerenciamento de Schema do Banco de Dados"
epic: "Fase 7: Integração com `modular-dashboard` como Microsserviço API"
status: done
priority: medium
dependencies: ["TASK-024", "TASK-030"]
assignee: Jules
---

### Descrição

Usar o evento `@app.on_event("startup")` para executar `CREATE EXTENSION` e `CREATE TABLE`.

### Critérios de Aceitação

- [ ] Evento `@app.on_event("startup")` está implementado em `src/main.py`.
- [ ] Comando `CREATE EXTENSION IF NOT EXISTS vector;` é executado no startup.
- [ ] Comando `CREATE TABLE IF NOT EXISTS ...` para a tabela de documentos é executado no startup.
- [ ] A lógica de criação de tabelas é idempotente (não falha se a extensão/tabela já existir).

### Arquivos Relevantes

* `src/main.py`
* `src/vector_store_handler.py` (para referência do schema)

### Relatório de Execução

Successfully implemented database schema management on application startup in `src/main.py`.
**1. Database Configuration (`src/db_config.py`):**
   - Created `src/db_config.py` to manage database connection settings (from environment variables) and the `asyncpg` connection pool.
   - Implemented `async def connect_to_db()` to create and assign the global `db_pool`.
   - Implemented `async def close_db_connection()` to close the `db_pool`.
   - Defined `EMBEDDING_DIMENSIONS` (defaulting to 384, configurable via env var).
**2. Startup Event (`@app.on_event("startup")` in `src/main.py`):**
   - Imported necessary functions and variables from `src.db_config`.
   - The `startup_db_event` function now:
       - Calls `await connect_to_db()`.
       - If the pool is available, acquires a connection and, within a transaction:
           - Executes `CREATE EXTENSION IF NOT EXISTS vector;`.
           - Executes `CREATE TABLE IF NOT EXISTS documents (...)` with columns: `id SERIAL PRIMARY KEY`, `filename TEXT`, `page_number INTEGER`, `text_content TEXT`, `metadata JSONB`, `embedding VECTOR(EMBEDDING_DIMENSIONS)`, `created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP`, and a `UNIQUE` constraint on `(filename, page_number)`.
       - Includes logging for successful DDL execution and error handling.
**3. Shutdown Event (`@app.on_event("shutdown")` in `src/main.py`):**
   - The `shutdown_db_event` function calls `await close_db_connection()` to gracefully close the database pool.
This setup ensures that the database connection is managed through the application lifecycle and the required schema (vector extension and documents table) is idempotently created at startup.
