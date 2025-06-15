---
id: TASK-014
title: "F7: Escrever Testes da API"
epic: "Fase 7: Integração com `modular-dashboard` como Microsserviço API"
status: backlog
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

(Esta seção deve ser deixada em branco no template)
