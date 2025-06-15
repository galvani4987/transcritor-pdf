---
id: TASK-013
title: "F7: Implementar Gerenciamento de Schema do Banco de Dados"
epic: "Fase 7: Integração com `modular-dashboard` como Microsserviço API"
status: backlog
priority: medium
dependencies: []
assignee: Jules
---

### Descrição

Usar o evento `@app.on_event("startup")` para executar `CREATE EXTENSION` e `CREATE TABLE`.

### Critérios de Aceitação

- [ ] Evento `@app.on_event("startup")` está implementado em `src/main.py`.
- [ ] Comando `CREATE EXTENSION IF NOT EXISTS vector;` é executado no startup.
- [ ] Comando `CREATE TABLE IF NOT EXISTS ...` para a tabela de documentos é executado no startup.
- [ ] A lógica de criação de tabelas é idempotente (não falha se a extensão/tabela já existir).

### Arquivos Relevantes

* `src/main.py`
* `src/vector_store_handler.py` (para referência do schema)

### Relatório de Execução

(Esta seção deve ser deixada em branco no template)
