---
id: TASK-026
title: "Doc Research: Celery (Asynchronous Task Queuing)"
epic: "Documentation"
status: done
priority: medium
dependencies: ["TASK-025"]
assignee: Jules
---

### Descrição

Research official documentation for Celery. Identify key concepts (tasks, workers, brokers, backends), setup, configuration with Redis as a broker, usage patterns for defining and calling tasks, and best practices relevant to its planned use in the 'transcritor-pdf' project for background PDF processing. Create a summary reference file named `docs/reference/celery_summary.txt`.

### Critérios de Aceitação

- [x] Official documentation website(s) for Celery identified and accessed (docs.celeryq.dev).
- [x] Key information relevant to the project (defining tasks, configuring Celery app, using Redis as broker, starting workers, calling tasks, monitoring tasks) reviewed.
- [x] Summary reference file `docs/reference/celery_summary.txt` created with key findings, relevant links, and code snippets for task definition and invocation.

### Arquivos Relevantes

* `ROADMAP.md` (Phase 9)
* `requirements.txt` (Celery will be added here)
* `docs/reference/celery_summary.txt`
* `docs/reference/redis_summary.txt` (Dependency)

### Relatório de Execução

Performed research on Celery, focusing on its core concepts, setup, and usage for asynchronous task processing, particularly with Redis as a broker and potential result backend.

Key areas researched include:

*   **Celery's Architecture:** Understanding of Tasks (the functions to be run asynchronously), Workers (processes executing tasks), the Broker (message transport like Redis or RabbitMQ), and the optional Backend (for storing task states and results).
*   **Installation:** How to install Celery core and its Redis dependencies (`pip install celery[redis]`).
*   **Application Setup:** Setting up a Celery application instance (`Celery(...)`), including essential configurations for `broker_url` (e.g., `'redis://localhost:6379/0'`) and `result_backend` (e.g., `'redis://localhost:6379/1'`). Also covered loading configuration from external files (`app.config_from_object`).
*   **Defining Tasks:** Using the `@app.task` decorator to define asynchronous tasks, including binding tasks (`@app.task(bind=True)`) for access to `self` for retries and custom state updates.
*   **Running Workers:** How to start and manage Celery workers from the command line (`celery -A your_app_module worker`), including setting log levels and concurrency.
*   **Calling Tasks:** Invoking tasks asynchronously using `.delay()` and the more versatile `.apply_async()` method, which allows for specifying countdowns, ETAs, and specific queues. Understanding and using the `AsyncResult` object to check task status, retrieve results, or get error information.
*   **Workflow Design (Canvas):** Introduction to Celery Canvas for designing complex workflows, including signatures (`.s()`), chains, groups, and chords.
*   **Redis-Specific Configurations:** Important considerations when using Redis, such as setting the `visibility_timeout` in `broker_transport_options` to prevent tasks from being re-processed prematurely and notes on Redis key eviction policies.
*   **Monitoring:** Overview of monitoring Celery applications, primarily using Flower (the real-time web UI) and Celery's command-line inspection tools.
*   **Optimization and Best Practices:** Covered key practices like designing idempotent tasks, appropriate configuration of `worker_prefetch_multiplier`, `task_acks_late`, and memory management for worker processes (`worker_max_tasks_per_child`, `worker_max_memory_per_child`).

A comprehensive summary of these findings has been documented in `docs/reference/celery_summary.txt`. This summary includes explanations of relevant concepts, Python code examples for Celery application setup, task definition, task invocation, result handling, and links to official Celery documentation pages for further details.
