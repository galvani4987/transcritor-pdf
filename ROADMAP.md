# Roadmap - Transcritor PDF

Este documento detalha as fases e tarefas planejadas para o desenvolvimento do projeto `transcritor-pdf`. Usaremos checkboxes (`[ ]` pendente, `[x]` concluído) para acompanhar o progresso. **Nota:** Requisitos atualizados em 21/04/2025 para incluir processamento página-a-página, objetivo final de RAG, e interação com Vector DB.

**Fase 0: Configuração Inicial e Planejamento**

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

**Fase 1: Tratamento da Entrada (Módulo `src/input_handler`)**

* [x] Adicionar dependência para manipulação de PDF (ex: `pypdfium2`) ao `requirements.txt` e instalar.
* [x] Implementar análise básica de argumentos de linha de comando (CLI) em `src/main.py` usando `argparse` para receber o caminho do arquivo PDF de entrada.
* [x] Criar `src/input_handler/pdf_splitter.py`.
* [x] **Implementar função em `pdf_splitter.py` para dividir um arquivo PDF de entrada em páginas individuais (salvando como imagens temporárias WebP em disco).**
* [x] Criar `src/input_handler/loader.py`.
* [x] Implementar função em `loader.py` para carregar uma imagem de página (a partir do caminho do arquivo temporário). Validar o input.
* [ ] Implementar tratamento de erros para caminhos inválidos, PDFs corrompidos ou tipos de arquivo não suportados.
* [x] Modificar o fluxo principal em `src/main.py` para:
    * Receber o caminho do PDF.
    * Chamar o `pdf_splitter` para obter os caminhos das páginas.
    * **Iterar sobre cada caminho de página**, chamando as fases seguintes (placeholders) para cada uma.
* [ ] Realizar commit das funcionalidades de tratamento de entrada e divisão de PDF.

**Fase 2: Pré-processamento por Página (Módulo `src/preprocessor`)**

* [x] Adicionar dependências de pré-processamento ao `requirements.txt` (ex: `pillow`) e instalar.
* [x] Criar `src/preprocessor/image_processor.py`.
* [x] Pesquisar e decidir sobre técnicas de pré-processamento de imagem para manuscritos. **(Concluído: Pesquisa indicou pipeline com Scikit-image: Deskew -> Grayscale -> Median -> CLAHE -> Sauvola)**
* [x] Adicionar dependência `scikit-image` ao `requirements.txt` e instalar.
* [ ] Implementar **Deskewing** (Correção de Inclinação) em `image_processor.py` (pode requerer pesquisa adicional de implementação com Scikit-image/OpenCV).
* [x] Implementar **Conversão para Escala de Cinza** em `image_processor.py`.
* [x] Implementar **Filtro de Mediana** (Redução de Ruído) em `image_processor.py` usando Scikit-image.
* [x] Implementar **CLAHE** (Melhora de Contraste) em `image_processor.py` usando Scikit-image.
* [x] Implementar **Binarização Sauvola** em `image_processor.py` usando Scikit-image.
* [ ] Implementar [Opcional] **Recorte de Bordas** em `image_processor.py`.
* [x] Integrar a chamada à função `preprocess_image` no loop de página em `src/main.py`.
* [ ] Realizar commit das funcionalidades de pré-processamento.
* [ ] _(Pendente)_ Pesquisar como usar `Docling` (ou similar) para análise de layout **em cada imagem de página** (detectar blocos de texto, áreas de assinatura).
* [ ] _(Pendente)_ Criar `src/preprocessor/layout_analyzer.py` (ou integrar).
* [ ] _(Pendente)_ Implementar a integração com `Docling` para obter informações de layout **por página**.

**Fase 3: Extração de Informações por Página (Módulo `src/extractor`)**

* [x] Criar `src/extractor/llm_client.py`.
* [x] Implementar a lógica para carregar a API Key do OpenRouter do `.env`.
* [x] Implementar a configuração e inicialização do cliente Langchain (OpenRouter).
* [x] Criar `src/extractor/text_extractor.py`.
* [x] Desenvolver prompt/cadeia Langchain para extrair texto (OCR) **da imagem da página pré-processada**.
* [ ] Criar `src/extractor/info_parser.py`.
* [ ] Desenvolver prompt/cadeia Langchain para analisar o texto extraído **da página** e identificar/extrair informações chave (Nome Cliente, Data, Assinatura?, Doenças?). **Considerar como lidar com informações que podem abranger múltiplas páginas (talvez extrair por página e agregar depois?).**
* [ ] Refinar prompts para precisão e custo **por página**.
* [ ] Implementar tratamento de erros para chamadas à API LLM.
* [ ] Integrar as etapas de extração no loop de página em `src/main.py`.
* [ ] Realizar commit das funcionalidades de extração por página.

**Fase 4: Tratamento da Saída para RAG (Módulo `src/output_handler`)**

* [ ] Criar `src/output_handler/formatter.py`.
* [ ] **Definir formato de saída estruturado (ex: lista de JSONs, um por página/chunk) otimizado para RAG.** Cada registro deve conter o texto extraído (ou chunks dele) e metadados essenciais (arquivo original, nº da página, data extraída, nome do cliente extraído, etc.).
* [ ] Implementar função em `formatter.py` para gerar essa saída estruturada a partir dos dados extraídos de cada página.
* [ ] Implementar a exibição (talvez resumida) do resultado no console.
* [ ] Implementar a opção de salvar a saída estruturada completa em um arquivo (ex: `.jsonl`).
* [ ] Integrar o tratamento de saída no final do processamento do PDF em `src/main.py`.
* [ ] Realizar commit das funcionalidades de tratamento de saída para RAG.

**Fase 5: Vetorização e Armazenamento (Módulo `src/vectorizer`)**

* [ ] Escolher biblioteca e modelo de embedding (ex: `sentence-transformers`, `openai embeddings`, ou via OpenRouter se disponível). Adicionar dependência ao `requirements.txt` e instalar.
* [ ] Escolher Vector DB (ex: ChromaDB, FAISS - locais; Pinecone, Weaviate - cloud). Adicionar dependência se local (`chromadb`, `faiss-cpu`/`faiss-gpu`) e instalar.
* [ ] Criar módulo `src/vectorizer/` com `__init__.py`.
* [ ] Criar `src/vectorizer/embedding_generator.py`.
* [ ] Implementar lógica para gerar embeddings para os chunks de texto da saída formatada (Fase 4).
* [ ] Criar `src/vectorizer/vector_store_handler.py`.
* [ ] Implementar lógica para inicializar/conectar ao Vector DB escolhido.
* [ ] Implementar lógica para adicionar/atualizar os vetores e metadados no Vector DB.
* [ ] Integrar a etapa de vetorização no fluxo principal (`main.py`), provavelmente após a Fase 4.
* [ ] Realizar commit da funcionalidade de vetorização.

**Fase 6: Integração Final, Testes e Refinamento**

* [ ] Revisar a integração de todos os módulos no pipeline principal (loop por página + vetorização).
* [ ] Adicionar logging adequado.
* [ ] Criar a estrutura da pasta `tests/`.
* [ ] Escrever testes unitários e de integração (incluindo vetorização).
* [ ] Refatorar código (clareza, eficiência, manutenibilidade).
* [ ] Adicionar/Melhorar docstrings.
* [ ] Atualizar `README.md` com instruções de uso completas.
* [ ] Realizar commit da versão final do CLI.

**Fase 7: Futuro - Integração com `modular-dashboard`**

* [ ] Analisar requisitos para integração.
* [ ] Definir API/interface programática.
* [ ] Refatorar código para ser reutilizável como biblioteca.
* [ ] Implementar a interface de integração.