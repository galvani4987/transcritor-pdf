# Guia de Testes Finais - Transcritor PDF

Este documento fornece um checklist de testes para garantir que o projeto `transcritor-pdf` está funcionando corretamente em um ambiente real e está pronto para integração ou produção. Siga estas etapas para verificar todas as funcionalidades críticas.

## 1. Setup e Pré-requisitos

Antes de iniciar os testes, garanta que:

*   **Variáveis de Ambiente**: O arquivo `.env` está configurado corretamente com todas as chaves de API necessárias (e.g., OpenRouter), credenciais do banco de dados (PostgreSQL), e configurações do Redis/Celery.
*   **Serviços Externos**: Se não estiver usando Docker para todos os serviços, certifique-se de que instâncias do PostgreSQL e Redis estejam acessíveis e configuradas conforme o `.env`.
*   **Repositório Atualizado**: Você está com a versão mais recente do código do `transcritor-pdf` e, se estiver testando a integração, do `modular-dashboard-adv`.
*   **Dependências Instaladas**: Se estiver rodando localmente (fora do Docker), todas as dependências Python do `requirements.txt` estão instaladas em seu ambiente virtual.
*   **Arquivos de Teste**: Tenha alguns arquivos PDF de exemplo disponíveis (simples e, se possível, complexos) para os testes de processamento.

## 2. Execução de Testes Automatizados

Esta seção descreve como executar os testes automatizados existentes para verificar funcionalidades chave.

*   **testar execução da suíte de testes completa**: você deve navegar até o diretório raiz do projeto no terminal e executar o comando `pytest tests/`. Isso rodará todos os arquivos de teste dentro do diretório `tests/`, incluindo testes de API, testes de unidade de módulos individuais e o teste de smoke. Verifique se todos os testes passam sem erros.
    *   *Comando*: `pytest tests/`
    *   *Resultado Esperado*: Todos os testes concluídos com sucesso (e.g., "X tests passed").
*   **testar execução do teste de smoke (se executado separadamente)**: você deve executar o script `tests/smoke_test.py` diretamente se ele não for coberto pelo `pytest tests/` ou se precisar de um ambiente específico (como um container já rodando). O smoke test geralmente verifica a disponibilidade básica do serviço e o endpoint de health.
    *   *Comando (exemplo)*: `python tests/smoke_test.py`
    *   *Resultado Esperado*: O script termina sem erros, indicando que o serviço está respondendo corretamente ao health check.

## 3. Testes Manuais dos Endpoints da API

Teste cada endpoint da API manualmente para garantir que eles se comportam conforme o esperado em um ambiente real. Use uma ferramenta como `curl`, Postman, ou Insomnia.

*   **testar endpoint `/health`**: você deve fazer uma requisição GET para `/health/` e verificar se retorna status HTTP 200 e o corpo JSON `{"status": "healthy"}`.
    *   *Método*: `GET`
    *   *URL*: `http://<host>:<port>/health/`
    *   *Resultado Esperado*: Status 200, Corpo: `{"status": "healthy"}`.
*   **testar endpoint `/process-pdf/` (submissão com sucesso)**: você deve enviar um arquivo PDF válido (e.g., `sample.pdf`) através de uma requisição POST para `/process-pdf/` (multipart/form-data). Verifique se retorna um status HTTP 200 (ou 202, dependendo da implementação final para indicar aceitação para processamento assíncrono) e um corpo JSON contendo um `task_id` (e.g., `{"task_id": "some-uuid"}`).
    *   *Método*: `POST`
    *   *URL*: `http://<host>:<port>/process-pdf/`
    *   *Corpo*: `multipart/form-data` com um campo `file` contendo o PDF.
    *   *Resultado Esperado*: Status 200 (ou 202), Corpo: `{"task_id": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"}`.
*   **testar endpoint `/process-pdf/` (sem arquivo anexado)**: você deve fazer uma requisição POST para `/process-pdf/` sem anexar um arquivo. Verifique se retorna um status HTTP 422 (Unprocessable Entity) com uma mensagem de erro apropriada no corpo JSON indicando que o arquivo é obrigatório.
    *   *Método*: `POST`
    *   *URL*: `http://<host>:<port>/process-pdf/`
    *   *Corpo*: `multipart/form-data` sem o campo `file`.
    *   *Resultado Esperado*: Status 422, mensagem de erro relevante.
*   **testar endpoint `/process-pdf/` (tipo de arquivo inválido)**: você deve enviar um arquivo que não seja PDF (e.g., um arquivo `.txt` ou `.jpg`) para `/process-pdf/`. Verifique se retorna um status HTTP 400 (Bad Request) ou 422 com uma mensagem de erro indicando que o tipo de arquivo não é suportado.
    *   *Método*: `POST`
    *   *URL*: `http://<host>:<port>/process-pdf/`
    *   *Corpo*: `multipart/form-data` com um campo `file` contendo um arquivo não-PDF.
    *   *Resultado Esperado*: Status 400 ou 422, mensagem de erro relevante.
*   **testar endpoint `/process-pdf/status/{task_id}` (status PENDING)**: imediatamente após submeter um PDF com sucesso e obter um `task_id`, faça uma requisição GET para `/process-pdf/status/<task_id_recebido>`. Verifique se o status HTTP é 200 e se o corpo JSON indica o status `PENDING` (ou o estado inicial definido para tarefas na fila).
    *   *Método*: `GET`
    *   *URL*: `http://<host>:<port>/process-pdf/status/<task_id>`
    *   *Resultado Esperado*: Status 200, Corpo: `{"task_id": "<task_id>", "status": "PENDING", "result": null}` (ou similar).
*   **testar endpoint `/process-pdf/status/{task_id}` (status SUCCESS)**: após aguardar tempo suficiente para o processamento do PDF ser concluído, faça uma requisição GET para `/process-pdf/status/<task_id_recebido>`. Verifique se o status HTTP é 200 e se o corpo JSON indica o status `SUCCESS` (ou `COMPLETED`) e contém o resultado do processamento (e.g., informações sobre os chunks armazenados ou uma mensagem de sucesso).
    *   *Método*: `GET`
    *   *URL*: `http://<host>:<port>/process-pdf/status/<task_id>`
    *   *Resultado Esperado*: Status 200, Corpo: `{"task_id": "<task_id>", "status": "SUCCESS", "result": "Processamento concluído..."}` (ou similar).
*   **testar endpoint `/process-pdf/status/{task_id}` (status FAILURE)**: se for possível simular uma falha no processamento de um PDF (e.g., um PDF corrompido que passe na validação inicial mas falhe no pipeline), submeta tal PDF, obtenha o `task_id`, e então consulte o status. Verifique se o status HTTP é 200 e se o corpo JSON indica `FAILURE` e uma mensagem de erro.
    *   *Método*: `GET`
    *   *URL*: `http://<host>:<port>/process-pdf/status/<task_id>`
    *   *Resultado Esperado*: Status 200, Corpo: `{"task_id": "<task_id>", "status": "FAILURE", "result": "Mensagem de erro detalhada..."}`.
*   **testar endpoint `/process-pdf/status/{task_id}` (ID de tarefa inválido/desconhecido)**: faça uma requisição GET para `/process-pdf/status/uuid-invalido-ou-nao-existente`. Verifique se retorna um status HTTP 404 (Not Found) com uma mensagem de erro indicando que a tarefa não foi encontrada.
    *   *Método*: `GET`
    *   *URL*: `http://<host>:<port>/process-pdf/status/invalid-task-id`
    *   *Resultado Esperado*: Status 404, Corpo: `{"detail": "Task not found"}` (ou similar).

## 4. Teste de Processamento de PDF End-to-End

Esta seção foca em verificar todo o fluxo de processamento de um PDF, desde a submissão até o armazenamento final dos dados.

*   **testar processamento completo de um PDF simples (e.g., 1-3 páginas, texto claro)**:
    1.  Você deve obter um arquivo PDF simples e pequeno.
    2.  Submeta este PDF através do endpoint `POST /process-pdf/` e guarde o `task_id` retornado.
    3.  Monitore o status da tarefa usando `GET /process-pdf/status/{task_id}` até que o status seja `SUCCESS`.
    4.  Após a conclusão com sucesso, você deve conectar-se diretamente ao banco de dados PostgreSQL (usando `psql`, DBeaver, pgAdmin, etc.).
    5.  Consulte a tabela `document_chunks` (ou o nome configurado para a tabela de chunks vetorizados) filtrando pelo nome do arquivo ou metadados associados ao PDF submetido (se disponíveis e armazenados).
    6.  Verifique se os chunks de texto extraídos do PDF estão presentes, se os embeddings correspondentes foram gerados (a coluna de embedding não deve estar vazia/nula), e se metadados como número da página estão corretos.
    *   *Resultado Esperado*: O PDF é processado com sucesso, e os dados extraídos e vetorizados são corretamente armazenados e podem ser recuperados do banco de dados.
*   **testar processamento completo de um PDF mais complexo (opcional, e.g., múltiplas colunas, imagens, tabelas, >10 páginas)**:
    1.  Você deve obter um arquivo PDF que represente um caso de uso mais desafiador.
    2.  Repita os passos de submissão, monitoramento de status e verificação no banco de dados, como descrito para o PDF simples.
    3.  Preste atenção especial à qualidade da extração de texto, à segmentação em chunks e à integridade dos metadados para páginas com layouts complexos.
    *   *Resultado Esperado*: O PDF complexo é processado, e os dados, mesmo de layouts variados, são razoavelmente bem extraídos e armazenados. Pode haver algumas imperfeições, mas o sistema não deve falhar catastroficamente.

## 5. Verificação do Processamento Assíncrono

Verifique se os componentes de processamento assíncrono (Celery e Redis) estão funcionando corretamente.

*   **testar atividade dos workers Celery**:
    1.  Você deve acessar os logs do(s) contêiner(es) ou processo(s) onde os workers Celery estão rodando.
    2.  Após submeter um PDF para processamento via API (endpoint `/process-pdf/`), observe os logs dos workers.
    3.  Você deve verificar se os workers detectam a nova tarefa, iniciam seu processamento (logs indicando `Task received`, `Processing task_id`, etc.) e, eventualmente, a concluem (com sucesso ou falha, que também deve ser logado).
    *   *Resultado Esperado*: Logs dos workers Celery mostram o ciclo de vida da tarefa sendo processado (recebimento, execução, finalização).
*   **testar interação com Redis (Broker da Fila)**:
    1.  Se você tiver ferramentas de monitoramento para o Redis (como `redis-cli MONITOR`, ou uma interface gráfica), utilize-as para observar as filas.
    2.  Após submeter uma tarefa, você deve verificar se a tarefa aparece na fila do Celery gerenciada pelo Redis.
    3.  Após um worker pegar a tarefa, ela deve ser removida da fila principal (pode ir para um estado de "não reconhecida" temporariamente, dependendo da configuração do Celery, antes de ser confirmada como processada).
    *   *Resultado Esperado*: Tarefas são visíveis no Redis após a submissão e são consumidas pelos workers. Se o Flower (ferramenta de monitoramento do Celery) estiver configurado, ele pode ser uma alternativa mais fácil para visualizar o status das tarefas e workers.
*   **testar comportamento com múltiplos workers (se aplicável)**:
    1.  Se o sistema estiver configurado para rodar múltiplos workers Celery, submeta várias tarefas em rápida sucessão.
    2.  Você deve observar (via logs ou Flower) se as tarefas estão sendo distribuídas entre os diferentes workers disponíveis.
    *   *Resultado Esperado*: As tarefas são distribuídas entre os workers, demonstrando capacidade de processamento paralelo.

## 6. Verificação da Interação com o Banco de Dados

Garanta que a aplicação interage corretamente com o banco de dados PostgreSQL, incluindo a configuração inicial do schema e o armazenamento dos dados processados.

*   **testar criação automática do schema do banco de dados na inicialização**:
    1.  Você deve (idealmente com um banco de dados limpo ou sem as tabelas/extensões esperadas) iniciar a aplicação `transcritor-pdf` (seja localmente ou via Docker).
    2.  Conecte-se ao banco de dados PostgreSQL usando uma ferramenta de administração (e.g., `psql`, DBeaver, pgAdmin).
    3.  Verifique se a extensão `vector` foi criada/habilitada no schema público (ou no schema configurado). Comando: `\dx` no psql ou verifique nas extensões pela interface gráfica.
    4.  Verifique se a tabela `document_chunks` (ou o nome configurado) foi criada com todas as colunas esperadas (e.g., `id`, `document_id`, `page_number`, `text_chunk`, `embedding`, `metadata`). Comando: `\d document_chunks` no psql.
    *   *Resultado Esperado*: A extensão `vector` está presente e a tabela `document_chunks` existe com a estrutura correta, indicando que o evento `@app.on_event("startup")` funcionou.
*   **testar armazenamento de dados após processamento de PDF bem-sucedido**:
    1.  Siga os passos da seção "Teste de Processamento de PDF End-to-End" para processar um PDF com sucesso.
    2.  Após a confirmação de que a tarefa foi concluída (`SUCCESS`), conecte-se ao banco de dados.
    3.  Execute uma consulta SQL para buscar os registros na tabela `document_chunks` que correspondem ao PDF processado (e.g., `SELECT * FROM document_chunks WHERE document_id = 'nome_do_pdf' OR metadata @> '{"source": "nome_do_pdf"}';` - ajuste a query conforme a estrutura de metadados).
    4.  Você deve verificar se:
        *   Existem múltiplos registros, correspondendo aos chunks extraídos.
        *   A coluna `text_chunk` contém o texto extraído.
        *   A coluna `embedding` não está vazia/nula e contém vetores (geralmente representados como arrays de números).
        *   Metadados como `page_number` e `source` (nome do arquivo) estão corretos.
    *   *Resultado Esperado*: Os dados extraídos do PDF, incluindo os embeddings vetoriais, estão corretamente persistidos na tabela `document_chunks`.
*   **testar consistência dos dados (se aplicável)**:
    1.  Se houver lógica para evitar duplicatas ou para atualizar registros existentes, você deve testar esses cenários. Por exemplo, processar o mesmo PDF duas vezes.
    2.  Verifique o comportamento: os registros são duplicados, atualizados, ou a segunda tentativa é ignorada? Confirme se o comportamento observado está de acordo com o esperado.
    *   *Resultado Esperado*: O sistema lida com reprocessamento ou dados duplicados de forma consistente e previsível.

## 7. Validação do Ambiente Docker

Verifique se a aplicação `transcritor-pdf` e suas dependências (PostgreSQL, Redis, Celery workers) funcionam corretamente quando orquestradas via Docker Compose, especialmente no contexto do projeto `modular-dashboard-adv`.

*   **testar inicialização completa do ambiente com Docker Compose**:
    1.  Você deve navegar até o diretório raiz do projeto `modular-dashboard-adv` (que deve conter o `docker-compose.yml` principal que inclui o `transcritor-pdf` como um serviço).
    2.  Execute o comando para iniciar todos os serviços: `docker-compose up -d` (o `-d` é para modo detached, mas para testes iniciais, você pode preferir rodar sem `-d` para ver os logs de todos os serviços).
    3.  Verifique os logs de inicialização de cada contêiner relevante:
        *   `docker-compose logs transcritor-pdf-api` (ou o nome do serviço da API do transcritor)
        *   `docker-compose logs transcritor-pdf-worker` (ou o nome do serviço do worker Celery)
        *   `docker-compose logs postgres` (ou o nome do serviço do PostgreSQL)
        *   `docker-compose logs redis` (ou o nome do serviço do Redis)
    4.  Você deve verificar se todos os contêineres iniciam sem erros e se os logs indicam que os serviços estão prontos (e.g., API escutando na porta, worker Celery conectado ao broker, banco de dados aceitando conexões).
    *   *Resultado Esperado*: Todos os contêineres definidos no `docker-compose.yml` para o `transcritor-pdf` e suas dependências estão rodando e saudáveis.
*   **testar funcionalidade da API dentro do ambiente Docker**:
    1.  Após a inicialização bem-sucedida via Docker Compose, identifique a porta em que a API do `transcritor-pdf` está exposta no host (conforme definido na seção `ports` do `docker-compose.yml`).
    2.  Execute os testes manuais da API (conforme a Seção 3), direcionando as requisições para a porta exposta pelo Docker (e.g., `http://localhost:PORTA_EXPOSTA/health/`).
    *   *Resultado Esperado*: Todos os testes manuais da API passam quando executados contra o serviço rodando dentro do contêiner Docker.
*   **testar processamento end-to-end no ambiente Docker**:
    1.  Realize um teste de processamento completo de PDF (conforme a Seção 4), utilizando a API exposta pelo Docker.
    2.  Você deve verificar se o PDF é processado, os dados são armazenados no PostgreSQL (que também está rodando em Docker), e as tarefas são processadas pelos workers Celery (também em Docker).
    *   *Resultado Esperado*: O fluxo completo de processamento de PDF funciona corretamente dentro do ambiente containerizado, com todos os serviços interagindo como esperado.
*   **testar comunicação QRCodeentre os contêineres**:
    1.  Durante o teste end-to-end, preste atenção aos logs dos diferentes serviços (`transcritor-pdf-api`, `transcritor-pdf-worker`, `postgres`, `redis`).
    2.  Você deve verificar se não há erros de rede ou conexão entre os contêineres (e.g., API não consegue se conectar ao Redis ou PostgreSQL, worker não consegue se conectar ao broker ou ao banco).
    *   *Resultado Esperado*: Os serviços se comunicam uns com os outros usando os nomes de serviço definidos no Docker Compose (e.g., `redis://redis:6379/0`, `postgresql://user:pass@postgres:5432/dbname`).
*   **testar parada e remoção dos contêineres**:
    1.  Após os testes, pare e remova os contêineres usando `docker-compose down`.
    2.  Verifique se todos os contêineres relacionados ao `transcritor-pdf` são parados e removidos. Se volumes persistentes forem usados, decida se devem ser removidos também (`docker-compose down -v`).
    *   *Resultado Esperado*: Os contêineres são parados e removidos corretamente, limpando o ambiente.
