---
id: TASK-021
title: "F9: Implementar Fila de Tarefas Assíncronas"
epic: "Fase 9: Otimização e Escalabilidade (Futuro)"
status: backlog
priority: medium
dependencies: []
assignee: Jules
---

### Descrição

Implementar uma fila de tarefas para processamento assíncrono de PDFs. Isso envolve:
*   Pesquisar e integrar uma biblioteca de fila de tarefas (ex: Celery com Redis).
*   Refatorar o endpoint `POST /process-pdf/` para adicionar a tarefa à fila e retornar um `task_id`.
*   Criar um novo endpoint `GET /process-pdf/status/{task_id}` para consultar o status.

### Critérios de Aceitação

- [ ] Pesquisa de bibliotecas de fila (Celery/Redis, RQ, etc.) concluída e decisão tomada.
- [ ] Biblioteca de fila e suas dependências (e.g., Redis) adicionadas ao `requirements.txt` e/ou `docker-compose.yml`.
- [ ] Biblioteca de fila integrada ao projeto (`src/main.py` e/ou novos módulos).
- [ ] Endpoint `POST /process-pdf/` modificado para enfileirar a tarefa de processamento de PDF (passando o conteúdo do arquivo ou um caminho para ele) e retornar um `task_id` e uma mensagem de sucesso imediata.
- [ ] Lógica de processamento de PDF (originalmente no endpoint `POST /process-pdf/` ou na função `process_pdf_pipeline`) refatorada para ser executada por um worker da fila de tarefas.
- [ ] Novo endpoint `GET /process-pdf/status/{task_id}` implementado para retornar o status da tarefa (ex: pendente, em progresso, concluído, falha) e, se concluído com sucesso, o resultado ou um link para ele.
- [ ] Configuração para os workers da fila de tarefas (e.g., comando para iniciá-los).

### Arquivos Relevantes

* `src/main.py`
* `requirements.txt`
* `docker-compose.yml` (se Redis/broker for containerizado)
* Novo(s) arquivo(s) para a configuração da fila e workers (e.g., `src/tasks.py`, `celery_app.py`)
* Arquivo onde `process_pdf_pipeline` está definida.

### Relatório de Execução

(Esta seção deve ser deixada em branco no template)
