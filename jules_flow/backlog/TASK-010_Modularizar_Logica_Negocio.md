---
id: TASK-010
title: "F7: Modularizar Lógica de Negócio"
epic: "Fase 7: Integração com `modular-dashboard` como Microsserviço API"
status: backlog
priority: medium
dependencies: []
assignee: Jules
---

### Descrição

Refatorar o pipeline em uma função autônoma `process_pdf_pipeline(file_content: bytes)`.

### Critérios de Aceitação

- [ ] Função `process_pdf_pipeline(file_content: bytes)` criada.
- [ ] Lógica de pipeline existente refatorada para dentro da nova função.
- [ ] A função aceita `bytes` como conteúdo do arquivo.

### Arquivos Relevantes

* `src/main.py`
* Potencialmente outros arquivos onde o pipeline está atualmente definido.

### Relatório de Execução

(Esta seção deve ser deixada em branco no template)
