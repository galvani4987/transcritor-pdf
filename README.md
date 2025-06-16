# Transcritor PDF

Este projeto é uma ferramenta de linha de comando (CLI) em Python que visa processar arquivos PDF contendo documentos médicos manuscritos. Ele extrai o texto de cada página usando modelos de linguagem multimodais, analisa o texto para extrair informações chave (nome do cliente, data, etc.), formata a saída em chunks adequados para RAG (Retrieval-Augmented Generation) e, finalmente, gera embeddings vetoriais para esses chunks, armazenando-os em um banco de dados PostgreSQL com a extensão pgvector.

**Funcionalidades Principais:**

* Divide PDFs de múltiplas páginas em imagens individuais por página (formato WebP temporário).
* Aplica um pipeline de pré-processamento de imagem (Escala de Cinza, Filtro de Mediana, CLAHE, Binarização Sauvola) usando Scikit-image para melhorar a legibilidade.
* Utiliza um LLM (via Langchain/OpenAI API) para extrair o texto bruto de cada imagem de página pré-processada.
* Utiliza um LLM (via Langchain/OpenAI API) para analisar o texto extraído e identificar informações estruturadas (nome, data, assinatura, doenças).
* Formata os dados extraídos em chunks de texto com metadados associados, otimizados para RAG.
* Gera embeddings vetoriais para cada chunk de texto usando a API da OpenAI (`text-embedding-3-small`).
* Insere/Atualiza os chunks, metadados e embeddings em uma tabela PostgreSQL configurada com `pgvector`.

**Estrutura do Projeto:**

* `src/`: Código fonte principal da aplicação.
    * `input_handler/`: Módulos para lidar com a entrada (dividir PDF, carregar página).
        * `pdf_splitter.py`: Divide PDF em imagens de página.
        * `loader.py`: Carrega imagens de página.
    * `preprocessor/`: Módulo para pré-processar imagens de página.
        * `image_processor.py`: Aplica filtros (Median, CLAHE, Sauvola).
    * `extractor/`: Módulos para interagir com LLMs.
        * `llm_client.py`: Configura o cliente LLM (OpenAI/OpenRouter).
        * `text_extractor.py`: Extrai texto bruto da imagem via LLM.
        * `info_parser.py`: Extrai informações estruturadas do texto via LLM.
    * `output_handler/`: Módulo para formatar a saída.
        * `formatter.py`: Cria chunks formatados para RAG.
    * `vectorizer/`: Módulos para vetorização e armazenamento.
        * `embedding_generator.py`: Gera embeddings via API OpenAI.
        * `vector_store_handler.py`: Interage com o banco de dados PostgreSQL/pgvector.
    * `main.py`: Ponto de entrada da aplicação CLI e orquestrador do pipeline.
* `tests/`: Testes unitários e de integração (usando `pytest`).
* `requirements.txt`: Lista de dependências Python do projeto.
* `.env`: Arquivo para armazenar segredos (API keys, credenciais de DB) - **NÃO versionar no Git!**
* `.gitignore`: Especifica arquivos e diretórios a serem ignorados pelo Git.
* `ROADMAP.md`: Detalha as fases de desenvolvimento do projeto.

**Instalação:**

1.  **Clone o repositório:**

        git clone [https://github.com/galvani4987/transcritor-pdf.git](https://github.com/galvani4987/transcritor-pdf.git)
        cd transcritor-pdf

2.  **Crie e ative um ambiente virtual:**

        python -m venv .venv
        # Linux/macOS:
        source .venv/bin/activate
        # Windows:
        # .\.venv\Scripts\activate

3.  **Instale as dependências:**

        pip install -r requirements.txt

**Configuração:**

1.  **Crie um arquivo `.env`** na raiz do projeto.
2.  **Adicione as seguintes variáveis de ambiente** ao arquivo `.env`, substituindo pelos seus valores reais:

    ```dotenv
    # Chave da API OpenAI (necessária para embeddings e potencialmente LLMs)
    # Se usar OpenRouter para LLMs, esta chave pode ser a do OpenRouter se ele usar a API compatível OpenAI.
    OPENAI_API_KEY="sk-..."

    # Credenciais do Banco de Dados PostgreSQL (com pgvector)
    DB_HOST="localhost"        # Ou o endereço do seu servidor DB
    DB_PORT="5432"             # Ou a porta do seu servidor DB
    DB_NAME="nome_do_seu_banco" # Nome do banco de dados
    DB_USER="usuario_do_banco"   # Usuário com permissão de escrita
    DB_PASSWORD="senha_do_usuario" # Senha do usuário

    # --- Opcional: Configuração do LLM via OpenRouter ---
    # Se quiser usar OpenRouter para os LLMs de extração/parsing (em vez da OpenAI direta)
    # OPENAI_BASE_URL="https://openrouter.ai/api/v1"
    # OPENAI_MODEL_NAME="google/gemini-flash" # Ou outro modelo do OpenRouter
    ```

3.  **Configure o Banco de Dados PostgreSQL:**
    * Certifique-se de que o PostgreSQL (versão 16+ recomendada) esteja instalado e rodando.
    * Habilite a extensão `pgvector`: `CREATE EXTENSION IF NOT EXISTS vector;`
    * Crie a tabela para armazenar os chunks e vetores (ajuste nomes e dimensão do vetor conforme necessário):

            CREATE TABLE your_vector_table ( -- Use o nome real da tabela!
                chunk_id TEXT PRIMARY KEY,
                text_content TEXT,
                metadata JSONB,
                embedding_vector VECTOR(1536) -- Dimensão para text-embedding-3-small
            );
            -- Opcional: Crie um índice para busca eficiente
            -- CREATE INDEX ON your_vector_table USING hnsw (embedding_vector vector_l2_ops);
            -- CREATE INDEX ON your_vector_table USING ivfflat (embedding_vector vector_l2_ops) WITH (lists = 100);

**CLI Usage:**

Execute o script a partir da raiz do projeto, passando o caminho para o arquivo PDF como argumento:

    # Certifique-se que o ambiente virtual está ativado
    python -m src.main /caminho/para/seu/documento.pdf

O script processará o PDF, exibirá logs no console indicando o progresso de cada etapa (divisão, pré-processamento, extração, formatação, embedding, armazenamento) e tentará inserir os dados no banco de dados configurado.

**API Usage**

Esta seção descreve como rodar e interagir com a API FastAPI fornecida pelo projeto.

**Rodando a API Localmente:**

Para rodar a API localmente com recarregamento automático durante o desenvolvimento, use Uvicorn:

```bash
uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload
```

A API estará acessível em `http://localhost:8000`.

**Endpoints:**

1.  **Health Check**
    *   **Propósito:** Verificar o status operacional da API.
    *   **Método:** `GET`
    *   **Caminho:** `/health`
    *   **Resposta (200 OK):**
        ```json
        {"status": "healthy"}
        ```
    *   **Exemplo `curl`:**
        ```bash
        curl http://localhost:8000/health
        ```

2.  **Processar PDF**
    *   **Propósito:** Fazer upload de um arquivo PDF, processá-lo para extrair texto e informações, gerar embeddings e armazená-los no banco de dados.
    *   **Método:** `POST`
    *   **Caminho:** `/process-pdf/`
    *   **Corpo da Requisição:** `multipart/form-data` com uma chave `pdf_file` e o arquivo PDF como seu valor.
    *   **Resposta de Sucesso (200 OK):**
        ```json
        {
            "message": "PDF processed and data stored successfully.",
            "file_id": "unique_id_of_the_file",
            "chunks_added": "count"
        }
        ```
    *   **Respostas de Erro:**
        *   `400 Bad Request`:
            ```json
            {"detail": "No PDF file provided."}
            ```
            ```json
            {"detail": "Invalid PDF file."}
            ```
        *   `500 Internal Server Error`:
            ```json
            {"detail": "Error processing PDF: <specific error>"}
            ```
            ```json
            {"detail": "Database connection error: <specific error>"}
            ```
    *   **Exemplo `curl`:**
        ```bash
        curl -X POST -F "pdf_file=@/caminho/para/seu/documento.pdf" http://localhost:8000/process-pdf/
        ```

**Testes:**

Para rodar os testes unitários (requer `pytest` instalado):

    # Certifique-se que o ambiente virtual está ativado
    pytest