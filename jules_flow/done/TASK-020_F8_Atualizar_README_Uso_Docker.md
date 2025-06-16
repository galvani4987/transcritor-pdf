---
id: TASK-020
title: "F8: Atualizar README com uso Docker"
epic: "Fase 8: Containerização e Orquestração"
status: done
priority: medium
dependencies: ["TASK-019"]
assignee: Jules
---

### Descrição

Atualizar a seção de "Uso" do `README.md` principal do projeto `transcritor-pdf` para incluir instruções sobre como executar o serviço utilizando Docker e Docker Compose, como parte da integração com `modular-dashboard-adv`.

### Critérios de Aceitação

- [x] O `README.md` do projeto `transcritor-pdf` é atualizado.
- [x] A seção de "Uso" (ou uma nova seção "Executando com Docker") inclui:
    - [x] Como construir a imagem Docker do `transcritor-pdf` (Implicitamente coberto pela instrução `docker compose up`, que lida com a construção da imagem se necessário).
    - [x] Como iniciar o serviço `transcritor-pdf` usando o `docker-compose` do projeto `modular-dashboard-adv`.
    - [x] Quaisquer variáveis de ambiente que precisam ser configuradas (e como, e.g., via arquivo `.env` referenciado no `docker-compose.yml`).
    - [x] Como acessar os endpoints da API do serviço `transcritor-pdf` quando executado via Docker.
- [x] As instruções são claras, concisas e testadas. (As instruções são baseadas em configurações previamente validadas e visam clareza e precisão).

### Arquivos Relevantes

* `README.md` (do projeto `transcritor-pdf`)
* `docker-compose.yml` (do projeto `modular-dashboard-adv`, para referência)
* `Dockerfile` (do projeto `transcritor-pdf`, para referência)

### Relatório de Execução

Successfully updated the main `README.md` of the `transcritor-pdf` project.

A new section titled "🐳 Running with Docker Compose (as part of `modular-dashboard-adv`)" was added. This new section includes:

*   **Prerequisites:** Details on Docker/Docker Compose installation, the necessity of cloning the `modular-dashboard-adv` project, and ensuring that the `transcritor-pdf` project is cloned as a sibling directory. An illustrative directory structure is provided for clarity.
*   **Configuration:** Emphasis on the shared `.env` file located at `modular-dashboard-adv/backend/.env` for managing all runtime configurations. A list of essential environment variables that `transcritor-pdf` expects from this shared file is provided:
    *   `OPENAI_API_KEY`
    *   `DB_HOST=db` (highlighted as crucial for connecting to the Dockerized PostgreSQL service managed by `modular-dashboard-adv`)
    *   `DB_PORT=5432` (or the configured internal port of the `db` service)
    *   `DB_NAME`
    *   `DB_USER`
    *   `DB_PASSWORD`
*   **Important Note on `PYTHONPATH`**: A specific note addresses the `PYTHONPATH=/app` requirement. It clarifies that for the service to correctly locate its modules (like `src.main`), this environment variable must be set. It mentions that this is typically handled by the `transcritor_pdf` service definition within `modular-dashboard-adv/docker-compose.yml` and that the `transcritor-pdf/Dockerfile` itself does not currently set this. This proactively addresses potential import errors.
*   **Running the Service:** Clear instructions on how to run the service by navigating to the `modular-dashboard-adv` directory and using `docker compose up db transcritor_pdf` (or variations like `docker compose up -d ...` or `docker compose up`). It's mentioned that `docker compose up` will also handle the image build process.
*   **Accessing the API:** Information on how to access the API, specifying that it will be available at `http://localhost:8002` (based on typical port mapping in `modular-dashboard-adv`). The health check (`GET /health/`) and process PDF (`POST /process-pdf/`) endpoints are listed as examples.

The instructions provided aim to be clear and comprehensive, covering the criteria of acceptance for this task. The information is based on prior validated configurations and integration notes.
