---
id: TASK-037
title: "DOC: Update README - API Health Path"
epic: "System Consistency & Correction"
status: done
priority: low
dependencies: []
assignee: Jules
---

### Descrição

`README.md` shows API health check path as `/health` in one section, but `src/main.py` implements it as `/health/`.

### Critérios de Aceitação

- [ ] All mentions of the health check API path in `README.md` are corrected to `/health/`.

### Arquivos Relevantes

* `README.md`

### Relatório de Execução

Subtask completed successfully.
- Corrected the health check API path in `README.md` from `/health` to `/health/` in the "API Usage" -> "Endpoints" section.
- Updated the corresponding `curl` example to use `/health/`.
- Updated the example JSON response in that section from `{"status": "healthy"}` to `{"status": "ok"}` to match the actual API behavior.
The README.md now consistently reflects the correct health check endpoint details.
