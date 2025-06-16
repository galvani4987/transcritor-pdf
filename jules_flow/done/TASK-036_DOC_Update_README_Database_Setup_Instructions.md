---
id: TASK-036
title: "DOC: Update README - Database Setup Instructions"
epic: "System Consistency & Correction"
status: done
priority: medium
dependencies: ["TASK-033"]
assignee: Jules
---

### Descrição

`README.md` instructs manual table creation (`CREATE TABLE your_vector_table...`). This is outdated as `src/main.py` handles `vector` extension and `documents` table creation on startup.

### Critérios de Aceitação

- [ ] "Configure o Banco de Dados PostgreSQL" section in `README.md` is updated.
- [ ] README clarifies that the API creates the 'vector' extension and the 'documents' table.
- [ ] README specifies the correct table name ('documents') and its finalized schema.
- [ ] README still notes that PostgreSQL server, database instance, and user credentials need manual setup.

### Arquivos Relevantes

* `README.md`

### Relatório de Execução

Subtask completed successfully.
- Updated the "Configure o Banco de Dados PostgreSQL" section in `README.md`.
- Removed manual `CREATE TABLE` instructions for the 'documents' table.
- Clarified that the application manages the creation of the 'vector' extension and 'documents' table.
- Specified the correct schema for the 'documents' table (PK `chunk_id`, vector col `embedding VECTOR(1536)`).
- Retained instructions for users to set up PostgreSQL server, DB instance, user, and .env variables.
- Removed obsolete manual index creation note.
The README now accurately reflects the current automated database schema setup.
