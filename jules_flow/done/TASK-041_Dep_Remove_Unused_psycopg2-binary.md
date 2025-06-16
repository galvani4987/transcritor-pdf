---
id: TASK-041
title: "Dep: Remove Unused psycopg2-binary"
epic: "System Consistency & Correction"
status: done
priority: low
dependencies: []
assignee: Jules
---

### Descrição

`psycopg2-binary` is listed in `requirements.txt` but `asyncpg` is used for runtime database operations. `psycopg2` appears unused.

### Critérios de Aceitação

- [ ] A final global search for `psycopg2` imports in the entire project is performed.
- [ ] If confirmed unused, `psycopg2-binary` is removed from `requirements.txt`.

### Arquivos Relevantes

* `requirements.txt`

### Relatório de Execução

Subtask completed successfully.
- Performed a global search for `psycopg2` imports in all `*.py` files within `src/` and `tests/`.
- Confirmed no functional imports of `psycopg2` were found.
- Removed the line `psycopg2-binary     # Driver Sync PostgreSQL (pode ser necessário para compatibilidade ou ferramentas)` from `requirements.txt`.
The unused `psycopg2-binary` dependency has been removed.
