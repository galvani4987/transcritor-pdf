---
id: TASK-034
title: "DB: Correct Default Embedding Dimension"
epic: "System Consistency & Correction"
status: done
priority: high
dependencies: []
assignee: Jules
---

### Descrição

`src/db_config.py` defaults `EMBEDDING_DIMENSIONS` to 384. Project documentation and OpenAI model `text-embedding-3-small` use 1536 dimensions. This mismatch will cause errors if the env var is not explicitly set.

### Critérios de Aceitação

- [ ] Default for `EMBEDDING_DIMENSIONS` in `src/db_config.py` is changed from `384` to `1536`.

### Arquivos Relevantes

* `src/db_config.py`

### Relatório de Execução

Subtask completed successfully.
- Located `EMBEDDING_DIMENSIONS = int(os.getenv("EMBEDDING_DIMENSIONS", "384"))` in `src/db_config.py`.
- Changed the default value to 1536, resulting in:
  `EMBEDDING_DIMENSIONS = int(os.getenv("EMBEDDING_DIMENSIONS", "1536"))`.
This aligns the default dimension with the project's use of OpenAI `text-embedding-3-small`.
