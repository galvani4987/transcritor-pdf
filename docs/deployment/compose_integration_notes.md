# Docker Compose Integration Notes for transcritor-pdf with modular-dashboard-adv

This document provides analysis and guidance for integrating the `transcritor-pdf` service with the `docker-compose.yml` from the `galvani4987/modular-dashboard-adv` project.

## Existing `transcritor-pdf` Service Definition in `modular-dashboard-adv`

The `modular-dashboard-adv/docker-compose.yml` already includes a service definition for `transcritor_pdf`:

```yaml
# Snippet from modular-dashboard-adv/docker-compose.yml
services:
  # ... other services ...

  # Microsserviço para processamento e vetorização de PDFs.
  transcritor_pdf:
    # O contexto aponta para um diretório irmão, onde o Dockerfile do serviço deve residir.
    build:
      context: ../transcritor-pdf
      dockerfile: Dockerfile
    container_name: transcritor_pdf_service
    env_file:
      - ./backend/.env # Reutiliza o .env para acesso unificado ao banco de dados.
    depends_on:
      db:
        condition: service_healthy
    ports:
      - "8002:8002"
    volumes:
      - ../transcritor-pdf:/app # Monta o código fonte para desenvolvimento com live-reload.
    # O comando assume que o serviço expõe uma API FastAPI, alinhado com a arquitetura.
    command: uvicorn src.main:app --host 0.0.0.0 --port 8002 --reload
    networks:
      - app-network

  # ... db service and other definitions ...
```

## Analysis and Recommendations

This existing service definition is well-suited for a development environment. Here are key points for ensuring successful integration of the `transcritor-pdf` project:

**1. Directory Structure:**
   - The `build.context: ../transcritor-pdf` implies the following directory structure when both projects are checked out:
     ```
     your_workspace_directory/
     ├── modular-dashboard-adv/
     │   ├── backend/
     │   │   └── .env  <-- Shared .env file
     │   └── docker-compose.yml
     └── transcritor-pdf/   <-- Sibling directory to modular-dashboard-adv
         ├── Dockerfile
         ├── src/
         │   └── main.py
         └── requirements.txt
     ```
   - Ensure this structure is maintained for `docker compose up` to correctly build the `transcritor-pdf` image.

**2. Shared `.env` File:**
   - The `env_file: - ./backend/.env` means `transcritor-pdf` will use the environment variables defined in `modular-dashboard-adv/backend/.env`.
   - **Crucial:** This `.env` file *must* contain all necessary variables for `transcritor-pdf`. Specifically:
     - `DB_HOST=db` (This tells `transcritor-pdf` to connect to the `db` service defined in the same Docker Compose file).
     - `DB_PORT=5432` (The internal port of the PostgreSQL service).
     - `DB_NAME` (Should match `POSTGRES_DB` used by the `db` service, e.g., `appdb`).
     - `DB_USER` (Should match `POSTGRES_USER` used by the `db` service, e.g., `appuser`).
     - `DB_PASSWORD` (Should match `POSTGRES_PASSWORD` used by the `db` service).
     - `OPENAI_API_KEY` (Required by `transcritor-pdf` for LLM interactions).
     - Any other custom environment variables required by `transcritor-pdf`.

**3. `PYTHONPATH` (Recommended Addition):**
   - The `modular-dashboard-adv`'s main `api` service includes `PYTHONPATH=/app`.
   - If the `transcritor-pdf` `Dockerfile` sets `WORKDIR /app` and the application code (e.g., `main.py`) is within a subdirectory like `src` (i.e., `/app/src/main.py`), it's recommended to add `PYTHONPATH=/app` to the `transcritor_pdf` service definition's environment variables. This ensures Python can find `src.main`.
   - **Suggested addition to `transcritor_pdf` service in `docker-compose.yml`:**
     ```yaml
       environment:
         - PYTHONPATH=/app
         # Potentially other transcritor-pdf specific (non-secret) env vars if not in .env
     ```
     (This would be merged with `env_file` variables, with `environment` taking precedence for any overlapping keys).

**4. `Dockerfile` for `transcritor-pdf`:**
   - The `transcritor-pdf` project must have a `Dockerfile` at its root.
   - A recommended structure (from `docs/reference/docker_compose_summary.txt`) is a multi-stage build for efficiency and security. The `command` in the `docker-compose.yml` (`uvicorn src.main:app --host 0.0.0.0 --port 8002 --reload`) will override the `CMD` in the `Dockerfile` for development. The `Dockerfile` should still have its own production-ready `CMD`.
   - **Reference `Dockerfile` content (ensure this is present as `transcritor-pdf/Dockerfile`):**
     ```dockerfile
     # syntax=docker/dockerfile:1

     ARG PYTHON_VERSION=3.11
     ARG APP_PORT=8002 # Align with the port in compose command

     # ---- Builder Stage ----
     FROM python:${PYTHON_VERSION}-slim AS builder
     LABEL stage=builder

     ENV PYTHONDONTWRITEBYTECODE=1
     ENV PYTHONUNBUFFERED=1

     WORKDIR /opt/venv
     RUN python -m venv .

     COPY requirements.txt .
     RUN . /opt/venv/bin/activate && \
         pip install --no-cache-dir -U pip && \
         pip install --no-cache-dir -r requirements.txt

     # ---- Runtime Stage ----
     FROM python:${PYTHON_VERSION}-slim AS runtime

     ENV PYTHONDONTWRITEBYTECODE=1
     ENV PYTHONUNBUFFERED=1
     ENV APP_PORT=${APP_PORT}
     ENV PYTHONPATH=/app # Add if src is directly under /app

     WORKDIR /app

     ARG UID=10001
     RUN adduser \
         --disabled-password \
         --gecos "" \
         --home "/nonexistent" \
         --shell "/sbin/nologin" \
         --no-create-home \
         --uid "${UID}" \
         appuser

     COPY --from=builder /opt/venv /opt/venv
     COPY ./src /app/src # Assumes app code is in ./src

     USER appuser

     EXPOSE ${APP_PORT}

     # Default CMD for production (will be overridden by compose 'command' in dev)
     CMD ["/opt/venv/bin/python", "-m", "uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "${APP_PORT}"]
     ```

**Note:** The sample `Dockerfile` above includes `ENV PYTHONPATH=/app`. While this is a valid approach, the primary `Dockerfile` at the root of the `transcritor-pdf` repository (as of this writing) does not set `PYTHONPATH`, deferring this configuration to the Docker Compose environment (e.g., in `modular-dashboard-adv/docker-compose.yml`) to allow for flexibility. The key is to ensure `/app` is in Python's import path when the container runs.

**5. Port and Command:**
   - The service is configured to run on port `8002` and uses `uvicorn src.main:app ... --reload`. This aligns with a FastAPI application structure where `main.py` is inside a `src` directory.
   - The `volumes: - ../transcritor-pdf:/app` mount supports the `--reload` functionality.

By ensuring these points of alignment, particularly the directory structure, shared `.env` variables (with `DB_HOST=db`), and a compatible `Dockerfile` within `transcritor-pdf`, the service should integrate smoothly when `docker compose up` is run from the `modular-dashboard-adv` directory.
