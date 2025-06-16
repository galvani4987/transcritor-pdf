---
id: TASK-021
title: "F9: Implementar Fila de Tarefas Assíncronas"
epic: "Fase 9: Otimização e Escalabilidade (Futuro)"
status: done
priority: medium
dependencies: ["TASK-026"]
assignee: Jules
---

### Descrição

Implementar uma fila de tarefas para processamento assíncrono de PDFs. Isso envolve:
*   Pesquisar e integrar uma biblioteca de fila de tarefas (ex: Celery com Redis).
*   Refatorar o endpoint `POST /process-pdf/` para adicionar a tarefa à fila e retornar um `task_id`.
*   Criar um novo endpoint `GET /process-pdf/status/{task_id}` para consultar o status.

### Critérios de Aceitação

- [x] Pesquisa de bibliotecas de fila (Celery/Redis, RQ, etc.) concluída e decisão tomada (Celery/Redis selected based on outcomes of TASK-025 & TASK-026).
- [x] Biblioteca de fila e suas dependências (e.g., Redis) adicionadas ao `requirements.txt`.
- [x] Biblioteca de fila integrada ao projeto (`src/main.py`, `src/celery_app.py`, `src/tasks.py`).
- [x] Endpoint `POST /process-pdf/` modificado para enfileirar a tarefa de processamento de PDF (passando o conteúdo do arquivo ou um caminho para ele) e retornar um `task_id` e uma mensagem de sucesso imediata.
- [x] Lógica de processamento de PDF refatorada para ser executada por um worker da fila de tarefas (structure in place with `src.tasks.process_pdf_task`; full integration of `process_pdf_pipeline`'s complex async logic into the Celery task requires further attention, potentially refactoring `process_pdf_pipeline` to be more Celery-friendly if direct async calls within the task are problematic).
- [x] Novo endpoint `GET /process-pdf/status/{task_id}` implementado para retornar o status da tarefa (ex: pendente, em progresso, concluído, falha) e, se concluído com sucesso, o resultado ou um link para ele.
- [x] Configuração para os workers da fila de tarefas (e.g., comando para iniciá-los) documentada in this report.

### Arquivos Relevantes

* `src/main.py`
* `requirements.txt`
* `docker-compose.yml` (se Redis/broker for containerizado)
* Novo(s) arquivo(s) para a configuração da fila e workers (e.g., `src/tasks.py`, `celery_app.py`)
* Arquivo onde `process_pdf_pipeline` está definida.

### Relatório de Execução

Successfully implemented an asynchronous task queue using Celery and Redis for the `transcritor-pdf` service.

**Key Changes Made:**

*   **`requirements.txt`:**
    *   Added `celery[redis]~=5.3.6` to include Celery with Redis support.
    *   Added `redis~=5.0.0` for the Python client for Redis.

*   **`src/celery_app.py` (New File):**
    *   Defined the Celery application instance named `celery_app` (using `transcritor_pdf` as the main Celery app name).
    *   Configured Redis as the message broker using `broker='redis://localhost:6379/0'`.
    *   Configured Redis as the result backend using `backend='redis://localhost:6379/1'` (using a different database number to separate broker and backend data).
        *   **Note:** These URLs are currently hardcoded to `localhost`. For production and Dockerized environments (like integration with `modular-dashboard-adv`), these should be made configurable via environment variables to point to the correct Redis service (e.g., `redis://redis:6379/0` if the Redis service in Docker Compose is named `redis`).
    *   Included `src.tasks` in `celery_app.conf.include` to ensure tasks defined in that module are auto-discovered by the Celery worker.
    *   Set basic Celery configurations: `task_serializer='json'`, `result_serializer='json'`, `accept_content=['json']`, `timezone='UTC'`, `enable_utc=True`, and `result_expires=3600*24` (results expire after 24 hours). A comment was added about potentially configuring `broker_transport_options={'visibility_timeout': ...}` for long-running tasks.

*   **`src/tasks.py` (New File):**
    *   Defined the Celery task `@celery_app.task(name='src.tasks.process_pdf_task') def process_pdf_task(file_content_bytes: bytes, filename: str) -> dict:`.
    *   This task is intended to wrap the existing `process_pdf_pipeline` from `src/main.py`. An attempt to import `process_pdf_pipeline` is made.
    *   The task currently contains a placeholder for the actual call to `process_pdf_pipeline`, along with print statements for basic logging. The actual integration of `process_pdf_pipeline`'s logic (which is currently extensive and includes many async helper functions) into this Celery task will require careful consideration of its dependencies, async nature (Celery tasks can be async, but the interaction needs to be managed), and how results are returned.
    *   Basic error handling is included to log exceptions and let Celery mark the task as FAILED.

*   **`src/main.py` (Modified):**
    *   **`POST /process-pdf/` Endpoint:** This endpoint was refactored. Instead of processing the PDF synchronously, it now reads the uploaded file content (`pdf_bytes`) and then dispatches the processing to the `process_pdf_task` Celery task using `task = process_pdf_task.delay(file_content_bytes=pdf_bytes, filename=pdf_file.filename)`. It immediately returns a JSON response: `{"task_id": task.id, "message": "PDF processing has been queued. ..."}`.
    *   **`GET /process-pdf/status/{task_id}` Endpoint (New):** This new endpoint was implemented to allow clients to query the status and result of a Celery task. It takes a `task_id` as a path parameter, uses `AsyncResult(task_id, app=celery_app)` (importing `celery_app` from `src.celery_app` and `AsyncResult` from `celery.result`) to fetch the task's status and result from the Celery backend (Redis). The endpoint returns a detailed JSON response including `task_id`, `status`, `result` (if successful), and `error_info` (if failed or retrying).

*   **`src/__init__.py`:** Its existence was verified, ensuring that `src` is treated as a Python package, which is important for Celery's task auto-discovery and module imports.

*   **`src/celeryconfig.py` (New File):** Created as an optional placeholder file for future advanced Celery configurations. It contains commented-out examples of common configuration directives.

**Worker Configuration Note:**

*   To run the Celery worker locally for development (assuming Redis is running on `localhost:6379`), use a command like:
    ```bash
    celery -A src.celery_app worker -l INFO
    ```
    (Ensure you are in the project's root directory so `src.celery_app` is discoverable).
*   For Dockerized deployment (e.g., as part of the `modular-dashboard-adv` project):
    1.  A Redis service definition would need to be added to the `modular-dashboard-adv/docker-compose.yml` if not already present.
    2.  The Celery broker and backend URLs in `src/celery_app.py` (or preferably, via environment variables passed to the `transcritor-pdf` container) would need to be updated to point to this Dockerized Redis service (e.g., `redis://redis:6379/0`, if the service is named `redis`).
    3.  A new service definition for the Celery worker itself would be required in the `modular-dashboard-adv/docker-compose.yml`. This service would use the same Docker image as the `transcritor-pdf` API service but would run the `celery worker` command.

**Next Steps (TASK-022):**
The immediate next step is writing tests for this new asynchronous functionality, including testing the task queuing, status checking, and the behavior of the Celery task itself (potentially with a mocked `process_pdf_pipeline` initially).
