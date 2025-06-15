---
id: TASK-020
title: "F8: Atualizar README com uso Docker"
epic: "Fase 8: Containerização e Orquestração"
status: backlog
priority: medium
dependencies: ["TASK-019"]
assignee: Jules
---

### Descrição

Atualizar a seção de "Uso" do `README.md` principal do projeto `transcritor-pdf` para incluir instruções sobre como executar o serviço utilizando Docker e Docker Compose, como parte da integração com `modular-dashboard-adv`.

### Critérios de Aceitação

- [ ] O `README.md` do projeto `transcritor-pdf` é atualizado.
- [ ] A seção de "Uso" (ou uma nova seção "Executando com Docker") inclui:
    - [ ] Como construir a imagem Docker do `transcritor-pdf` (se o `docker-compose` não a construir automaticamente).
    - [ ] Como iniciar o serviço `transcritor-pdf` usando o `docker-compose` do projeto `modular-dashboard-adv`.
    - [ ] Quaisquer variáveis de ambiente que precisam ser configuradas (e como, e.g., via arquivo `.env` referenciado no `docker-compose.yml`).
    - [ ] Como acessar os endpoints da API do serviço `transcritor-pdf` quando executado via Docker.
- [ ] As instruções são claras, concisas e testadas.

### Arquivos Relevantes

* `README.md` (do projeto `transcritor-pdf`)
* `docker-compose.yml` (do projeto `modular-dashboard-adv`, para referência)
* `Dockerfile` (do projeto `transcritor-pdf`, para referência)

### Relatório de Execução

(Esta seção deve ser deixada em branco no template)
