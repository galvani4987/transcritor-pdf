---
id: TASK-015
title: "F7: Validar Conexão e Documentação"
epic: "Fase 7: Integração com `modular-dashboard` como Microsserviço API"
status: done
priority: medium
dependencies: ["TASK-013", "TASK-011", "TASK-024"] # Depends on DB schema and API endpoints
assignee: Jules
---

### Descrição

*   Revisar `vector_store_handler.py` para conexão via variáveis de ambiente.
*   Atualizar o `README.md` do projeto com a documentação da nova API.

### Critérios de Aceitação

- [ ] `vector_store_handler.py` utiliza variáveis de ambiente para todos os parâmetros de conexão do banco de dados (host, port, user, password, dbname).
- [ ] `README.md` inclui uma seção descrevendo a API.
- [ ] Documentação da API no `README.md` inclui:
    - [ ] Instruções de como executar a API.
    - [ ] Descrição dos endpoints disponíveis (`/health`, `/process-pdf/`).
    - [ ] Formato das requisições e respostas para cada endpoint.
    - [ ] Exemplos de uso (e.g., usando `curl` ou cliente Python).

### Arquivos Relevantes

* `src/vector_store_handler.py`
* `README.md`
* `.env.example` (se aplicável, para variáveis de ambiente)

### Relatório de Execução

(Esta seção deve ser deixada em branco no template)
