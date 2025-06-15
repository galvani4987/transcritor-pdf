---
id: TASK-019
title: "F8: Validar serviço com Docker Compose"
epic: "Fase 8: Containerização e Orquestração"
status: backlog
priority: medium
dependencies: ["TASK-017", "TASK-018"]
assignee: Jules
---

### Descrição

Validar que o serviço `transcritor-pdf` funciona corretamente em seu pipeline completo (upload, processamento, armazenamento) quando iniciado e gerenciado pelo `docker-compose` do projeto `modular-dashboard-adv`.

### Critérios de Aceitação

- [ ] O serviço `transcritor-pdf` é iniciado usando `docker-compose up` junto com outros serviços relevantes (como o banco de dados, se também containerizado).
- [ ] Um PDF de teste é enviado ao endpoint `/process-pdf/` do serviço `transcritor-pdf`.
- [ ] O processamento do PDF ocorre sem erros.
- [ ] Os dados extraídos e vetorizados são corretamente armazenados no banco de dados PostgreSQL.
- [ ] A interação com o banco de dados (acessado pelo `transcritor-pdf` containerizado) funciona como esperado.
- [ ] Logs do container do `transcritor-pdf` são verificados para confirmar a ausência de erros durante o processo.

### Arquivos Relevantes

* `docker-compose.yml` (do projeto `modular-dashboard-adv`)
* Logs do container do `transcritor-pdf`
* Interface de acesso ao banco de dados (e.g., DBeaver, pgAdmin) para verificar os dados.

### Relatório de Execução

(Esta seção deve ser deixada em branco no template)
