---
id: TASK-014
title: "F7: Escrever Testes da API"
epic: "Fase 7: Integração com `modular-dashboard` como Microsserviço API"
status: done
priority: medium
dependencies: ["TASK-011"] # Depends on endpoints being implemented
assignee: Jules
---

### Descrição

Implementar testes de integração para os endpoints (`/health`, `/process-pdf/`) usando o `TestClient` do FastAPI.

### Critérios de Aceitação

- [ ] Arquivo de teste para a API criado (e.g., `tests/test_api.py`).
- [ ] Teste de integração para o endpoint `GET /health/` implementado.
- [ ] Teste de integração para o endpoint `POST /process-pdf/` implementado (incluindo upload de arquivo mock).
- [ ] Testes cobrem cenários de sucesso e erro para o endpoint `/process-pdf/`.
- [ ] `TestClient` do FastAPI é utilizado para os testes.

### Arquivos Relevantes

* `src/main.py`
* `tests/test_api.py` (a ser criado)

### Relatório de Execução

Successfully implemented integration tests for API endpoints in `tests/test_api.py` using FastAPI's `TestClient`.

**1. Test Environment Setup:**
   - Added `httpx` to `requirements.txt` (pytest was already present).
   - Ensured `tests/` directory and `tests/__init__.py` exist.
   - Created `tests/test_api.py`.

**2. Implemented Tests for `GET /health/`:**
   - `test_health_check()`: Verifies 200 status and `{"status": "ok"}` response.

**3. Implemented Tests for `POST /process-pdf/` (Success Scenario):**
   - `test_process_pdf_success()`: Mocks a PDF file upload using `io.BytesIO`, verifies 200 status, and checks if the response JSON matches the expected output from the placeholder `process_pdf_pipeline`.

**4. Implemented Tests for `POST /process-pdf/` (Error Scenarios):**
   - `test_process_pdf_no_file_provided()`: Asserts 422 status when no file is uploaded.
   - `test_process_pdf_wrong_file_type()`: Asserts 415 status for non-PDF file uploads and checks the error detail.
   - `test_process_pdf_empty_file_content()`: Asserts 400 status for empty PDF file content and checks the error detail.
   - `test_process_pdf_no_filename()`: Asserts 400 status when no filename is provided and checks the error detail.

**5. Test Execution Note:**
   - Attempts to run `pytest` to confirm test execution failed due to a persistent error with the `run_in_bash_session` tool. The tests are written according to the API's current implementation and are expected to pass.

All criteria for writing the tests have been met.
