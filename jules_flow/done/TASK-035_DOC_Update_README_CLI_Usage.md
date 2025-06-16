---
id: TASK-035
title: "DOC: Update README - CLI Usage"
epic: "System Consistency & Correction"
status: done
priority: medium
dependencies: []
assignee: Jules
---

### Descrição

`README.md` contains a 'CLI Usage' section which is outdated as `argparse` logic was removed from `src/main.py` in favor of an API-first approach.

### Critérios de Aceitação

- [ ] "CLI Usage" section in `README.md` is removed or significantly revised to reflect the API-first nature and deprecation of CLI mode.

### Arquivos Relevantes

* `README.md`

### Relatório de Execução

Subtask completed successfully.
- Removed the obsolete "CLI Usage" section from `README.md`.
- Updated the main project description in `README.md` from "ferramenta de linha de comando (CLI)" to "API".
- Updated the description of `src/main.py` in the "Estrutura do Projeto" section to reflect it as the "Ponto de entrada da aplicação FastAPI".
The README now accurately reflects the API-first nature of the project.
