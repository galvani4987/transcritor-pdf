---
id: TASK-018
title: "F8: Escrever Teste de Smoke"
epic: "Fase 8: Containerização e Orquestração"
status: backlog
priority: medium
dependencies: ["TASK-017", "TASK-032"]
assignee: Jules
---

### Descrição

Criar um teste de smoke simples para validar que o serviço `transcritor-pdf` (quando containerizado e orquestrado) sobe corretamente e responde ao seu endpoint de saúde.

### Critérios de Aceitação

- [ ] Um script de teste de smoke é criado (e.g., em `tests/smoke_test.py` ou similar).
- [ ] O teste verifica se o container do `transcritor-pdf` está rodando conforme esperado após `docker-compose up`.
- [ ] O teste envia uma requisição ao endpoint `/health/` do serviço.
- [ ] O teste verifica se a resposta do endpoint `/health/` é bem-sucedida (e.g., status code 200).
- [ ] O script de teste é documentado, explicando como executá-lo.

### Arquivos Relevantes

* `tests/smoke_test.py` (a ser criado)
* `docker-compose.yml` (do projeto `modular-dashboard-adv`)
* `src/main.py` (para referência do endpoint `/health/`)

### Relatório de Execução

(Esta seção deve ser deixada em branco no template)
