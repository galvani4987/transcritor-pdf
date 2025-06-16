---
id: TASK-041
title: "Dep: Remove Unused psycopg2-binary"
epic: "System Consistency & Correction"
status: backlog
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

(Esta seção deve ser deixada em branco no template)
