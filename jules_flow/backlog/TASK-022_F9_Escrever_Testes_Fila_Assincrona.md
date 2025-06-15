---
id: TASK-022
title: "F9: Escrever Testes para Fila Assíncrona"
epic: "Fase 9: Otimização e Escalabilidade (Futuro)"
status: backlog
priority: medium
dependencies: ["TASK-021"]
assignee: Jules
---

### Descrição

Implementar testes para garantir que as tarefas são enfileiradas corretamente e que o status pode ser consultado, após a implementação da fila de tarefas assíncronas. Os testes devem cobrir:
*   Implementar testes para garantir que as tarefas são enfileiradas corretamente.
*   Implementar testes para que o status da tarefa pode ser consultado.

### Critérios de Aceitação

- [ ] Testes unitários/integração para o enfileiramento de tarefas no endpoint `POST /process-pdf/` são criados.
    - [ ] Verificar se o endpoint retorna `task_id` e status 202 (Accepted) ou similar.
    - [ ] Verificar se a tarefa foi efetivamente adicionada à fila (pode requerer mocking do broker da fila ou uma forma de inspecionar a fila).
- [ ] Testes para o endpoint `GET /process-pdf/status/{task_id}` cobrindo diferentes status de tarefa (pendente, em progresso, concluído com sucesso, falha) são criados.
    - [ ] Mockar diferentes estados da tarefa no backend para testar as respostas do endpoint de status.
- [ ] Testes que simulam a execução de uma tarefa pelo worker e verificam o resultado ou o status final são implementados.
    - [ ] Pode envolver o acionamento direto da função da tarefa (como um teste unitário) ou um teste de integração mais complexo com um worker de teste.
- [ ] Testes cobrem cenários de erro (e.g., falha no processamento da tarefa, task_id inválido).

### Arquivos Relevantes

* Arquivo(s) de teste existentes ou novo(s) (e.g., `tests/test_api.py`, `tests/test_tasks.py`).
* `src/main.py` (endpoints da API).
* Arquivo(s) de definição de tarefas (e.g., `src/tasks.py`).

### Relatório de Execução

(Esta seção deve ser deixada em branco no template)
