# Roadmap - Transcritor PDF

Este documento detalha as fases e tarefas planejadas para o desenvolvimento do projeto `transcritor-pdf`. Usaremos checkboxes (`[ ]` pendente, `[x]` concluído) para acompanhar o progresso. Nota: Requisitos atualizados em 24/04/2025 para incluir processamento página-a-página, objetivo final de RAG, e interação com Vector DB.

### Fase 0: Configuração Inicial e Planejamento

* [x] Definição do Escopo e Objetivos do Projeto (Atualizado: Saída para RAG + Vetorização)
* [x] Definição das Tecnologias Principais (Python, Langchain, Docling, OpenRouter)
* [x] Definição da Arquitetura Modular (src/input, preprocess, extract, output, vectorizer)
* [x] Criação da Estrutura Inicial de Pastas e Arquivos (`src/`, `main.py`, `__init__.py`)
* [x] Criação do `README.md` inicial
* [x] Criação do `requirements.txt` inicial (`langchain`, `openai`, `python-dotenv`)
* [x] Configuração do Repositório Git e Conexão com GitHub (`galvani4987/transcritor-pdf`)
* [x] Criação e Ativação do Ambiente Virtual (`.venv`)
* [x] Instalação das Dependências Iniciais (`pip install -r requirements.txt`)
* [x] Configuração do `.env` com a chave da API OpenRouter (feito pelo usuário)
* [x] Criação deste arquivo `ROADMAP.md`
* [x] Realizar o commit das atualizações no `ROADMAP.md` e arquivos de configuração.

### Fase 1: Tratamento da Entrada (Módulo `src/input_handler`)

* [x] Adicionar dependência para manipulação de PDF (ex: `pypdfium2`) ao `requirements.txt` e instalar.
* [x] Implementar análise básica de argumentos de linha de comando (CLI) em `src/main.py` usando `argparse` para receber o caminho do arquivo PDF de entrada.
* [x] Criar `src/input_handler/pdf_splitter.py`.
* [x] Implementar função em `pdf_splitter.py` para dividir um arquivo PDF de entrada em páginas individuais (salvando como imagens temporárias WebP em disco).
* [x] Criar `src/input_handler/loader.py`.
* [x] Implementar função em `loader.py` para carregar uma imagem de página (a partir do caminho do arquivo temporário). Validar o input.
* [x] Implementar tratamento de erros para caminhos inválidos, PDFs corrompidos ou tipos de arquivo não suportados. (Validação inicial e por página implementadas).
* [x] Modificar o fluxo principal em `src/main.py` para:
    * Receber o caminho do PDF.
    * Chamar o `pdf_splitter` para obter os caminhos das páginas.
    * Iterar sobre cada caminho de página, chamando as fases seguintes (placeholders) para cada uma.
* [x] **Escrever Testes Automatizados:** Implementar testes unitários para as funções de `pdf_splitter.py` e `loader.py`, garantindo a correta divisão do PDF e o carregamento das páginas.
* [x] Realizar commit das funcionalidades de tratamento de entrada e divisão de PDF.

### Fase 2: Pré-processamento por Página (Módulo `src/preprocessor`)

* [x] Adicionar dependências de pré-processamento ao `requirements.txt` (ex: `pillow`, `scikit-image`) e instalar.
* [x] Criar `src/preprocessor/image_processor.py`.
* [x] Pesquisar e decidir sobre técnicas de pré-processamento de imagem para manuscritos. (Concluído: Pesquisa indicou pipeline com Scikit-image: Deskew -> Grayscale -> Median -> CLAHE -> Sauvola)
* [x] Implementar pipeline de filtros (Deskew, Grayscale, Median, CLAHE, Sauvola) em `image_processor.py`.
* [x] Integrar a chamada à função `preprocess_image` no loop de página em `src/main.py`.
* [x] Pesquisar e implementar análise de layout com `Docling` ou similar. (Docling implemented via TASK-016, see `src/preprocessor/layout_analyzer.py` and `docs/reference/docling_summary.txt`)
* [x] **Escrever Testes Automatizados:** Criar testes unitários para a pipeline de `image_processor.py`, validando a aplicação de cada filtro.
* [x] Realizar commit das funcionalidades de pré-processamento.

### Fase 3: Extração de Informações por Página (Módulo `src/extractor`)

* [x] Criar `src/extractor/llm_client.py` para configurar e inicializar o cliente Langchain.
* [x] Criar `src/extractor/text_extractor.py` para extrair texto bruto da imagem via LLM.
* [x] Criar `src/extractor/info_parser.py` para extrair informações estruturadas do texto via LLM.
* [x] Refinar prompts para precisão e custo.
* [x] Integrar as chamadas de extração no loop de página em `src/main.py`.
* [x] **Escrever Testes Automatizados:** Implementar testes unitários para os módulos de extração, utilizando `mocks` para simular as respostas da API do LLM e validar o parsing dos resultados.
* [x] Realizar commit das funcionalidades de extração por página.

### Fase 4: Tratamento da Saída para RAG (Módulo `src/output_handler`)

* [x] Criar `src/output_handler/formatter.py`.
* [x] Definir e implementar a função para formatar os dados extraídos em chunks otimizados para RAG.
* [x] Integrar a formatação da saída no fluxo principal em `src/main.py`.
* [x] **Escrever Testes Automatizados:** Criar testes para o `formatter.py`, garantindo que os chunks e metadados sejam gerados na estrutura correta.
* [x] Realizar commit das funcionalidades de tratamento de saída para RAG.

### Fase 5: Vetorização e Armazenamento (Módulo `src/vectorizer`)

* [x] Adicionar dependências (`langchain-openai`, `asyncpg`) ao `requirements.txt`.
* [x] Criar `src/vectorizer/embedding_generator.py` para gerar embeddings.
* [x] Criar `src/vectorizer/vector_store_handler.py` para interagir com o PostgreSQL.
* [x] Integrar a etapa de vetorização no fluxo principal (`main.py`).
* [x] **Escrever Testes Automatizados:** Implementar testes para `embedding_generator.py` (com mock da API) e para `vector_store_handler.py` (testando a construção de queries SQL).
* [x] Realizar commit da funcionalidade de vetorização.

### Fase 6: Integração Final, Testes e Refinamento

* [x] Revisar a integração de todos os módulos no pipeline principal.
* [x] Adicionar logging adequado em todas as etapas.
* [x] Criar a estrutura da pasta `tests/`.
* [x] **Execução da Suíte de Testes:** Executar e garantir a passagem de todos os testes unitários criados nas fases anteriores.
* [x] **Escrever Testes de Integração:** Criar testes de integração para o pipeline completo (de ponta-a-ponta), usando um PDF de exemplo e mocks para serviços externos (LLM, DB).
* [x] Refatorar código (clareza, eficiência, manutenibilidade).
* [x] Adicionar/Melhorar docstrings.
* [x] Atualizar `README.md` com instruções de uso completas.
* [x] Realizar commit da versão final do CLI.

### Fase 7: Integração com `modular-dashboard` como Microsserviço API

* [x] Doc Research: Uvicorn (TASK-031)
* [x] **Atualizar Dependências da API:** (TASK-008)
    * [x] Adicionar `fastapi` e `uvicorn[standard]` ao arquivo `requirements.txt`.
* [x] **Refatorar Ponto de Entrada (`src/main.py`):** (TASK-009)
    * [x] Remover a lógica de `argparse` e instanciar a aplicação FastAPI.
* [x] **Modularizar Lógica de Negócio:** (TASK-010)
    * [x] Refatorar o pipeline em uma função autônoma `process_pdf_pipeline(file_content: bytes)`.
* [x] **Implementar Endpoints da API:** (TASK-011)
    * [x] Criar endpoint `GET /health/` para verificação de saúde.
    * [x] Criar endpoint `POST /process-pdf/` que aceita `UploadFile`.
* [x] **Implementar Tratamento de Erros da API:** (TASK-012)
    * [x] Definir e implementar respostas de erro padronizadas em JSON com códigos de status HTTP apropriados.
* [x] Doc Research: pgvector (Vector Storage with PostgreSQL) (TASK-024)
* [x] Doc Research: asyncpg (Async PostgreSQL Driver) (TASK-030)
* [x] **Implementar Gerenciamento de Schema do Banco de Dados:** (TASK-013)
    * [x] Usar o evento `@app.on_event("startup")` para executar `CREATE EXTENSION` e `CREATE TABLE`.
* [x] **Escrever Testes da API:** (TASK-014)
    * [x] Implementar testes de integração para os endpoints (`/health`, `/process-pdf/`) usando o `TestClient` do FastAPI.
* [x] **Validar Conexão e Documentação:** [x]
    * [x] Revisar `vector_store_handler.py` para conexão via variáveis de ambiente.
    * [x] Atualizar o `README.md` do projeto com a documentação da nova API.

### Fase 8: Containerização e Orquestração

* [x] Doc Research: Docker & Docker Compose (TASK-032) - see `docs/reference/docker_compose_summary.txt`
* [x] Criar um arquivo `.dockerignore` para otimizar o contexto de build.
* [x] Criar um `Dockerfile` para a aplicação Python.
* [x] Configurar a orquestração via o `docker-compose.yml` do projeto `modular-dashboard-adv`. (Integration notes prepared in TASK-017 for manual application based on existing definition in `modular-dashboard-adv`)
* [x] **Escrever Teste de Smoke:** Criar um teste simples para validar que o serviço containerizado sobe corretamente e responde ao endpoint de saúde. (Script `tests/smoke_test.py` created in TASK-018)
* [x] Validar que o serviço `transcritor-pdf` funciona corretamente quando iniciado pelo `docker-compose` principal.
* [x] Atualizar a seção de "Uso" do `README.md` para refletir a execução via Docker.

### Fase 9: Otimização e Escalabilidade (Futuro)

* [x] **Implementar Fila de Tarefas para Processamento Assíncrono:**
    * [x] Pesquisar e integrar uma biblioteca de fila de tarefas (ex: Celery com Redis).
    * [x] Refatorar o endpoint `POST /process-pdf/` para adicionar a tarefa à fila e retornar um `task_id`.
    * [x] Criar um novo endpoint `GET /process-pdf/status/{task_id}` para consultar o status.
* [x] **Escrever Testes para a Fila Assíncrona:**
    * [x] Implementar testes para garantir que as tarefas são enfileiradas corretamente e que o status pode ser consultado.
