---
id: TASK-011
title: "F7: Implementar Endpoints da API"
epic: "Fase 7: Integração com `modular-dashboard` como Microsserviço API"
status: backlog
priority: medium
dependencies: []
assignee: Jules
---

### Descrição

Implementar os endpoints da API:
*   Criar endpoint `GET /health/` para verificação de saúde.
*   Criar endpoint `POST /process-pdf/` que aceita `UploadFile`.

### Critérios de Aceitação

- [ ] Endpoint `GET /health/` está implementado e funcional.
- [ ] Endpoint `GET /health/` retorna um status de saúde (e.g., `{"status": "ok"}`).
- [ ] Endpoint `POST /process-pdf/` está implementado.
- [ ] Endpoint `POST /process-pdf/` aceita um `UploadFile`.
- [ ] Endpoint `POST /process-pdf/` utiliza a função `process_pdf_pipeline`.

### Arquivos Relevantes

* `src/main.py`

### Relatório de Execução

(Esta seção deve ser deixada em branco no template)
