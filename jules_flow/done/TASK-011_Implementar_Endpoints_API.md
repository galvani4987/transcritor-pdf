---
id: TASK-011
title: "F7: Implementar Endpoints da API"
epic: "Fase 7: Integração com `modular-dashboard` como Microsserviço API"
status: done
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

Successfully implemented two API endpoints in `src/main.py`:
1. `GET /health/`:
   - Defined an async function `health_check()`.
   - Decorated with `@app.get("/health/")`.
   - Returns `{"status": "ok"}`.
2. `POST /process-pdf/`:
   - Imported `UploadFile` and `File` from `fastapi`.
   - Defined an async function `process_pdf_endpoint(file: UploadFile = File(...))`.
   - Decorated with `@app.post("/process-pdf/")`.
   - Reads file bytes using `await file.read()`.
   - Calls the `process_pdf_pipeline(file_content=file_bytes, filename=file.filename)` function.
   - Returns the result from the pipeline.
   - Includes basic logging and a try/finally block to ensure file closure.
Changes were applied using `replace_with_git_merge_diff`.
