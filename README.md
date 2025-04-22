# Transcritor PDF

Este projeto visa extrair texto e informações chave (nome do cliente, data, etc.) de documentos médicos manuscritos digitalizados (fotos/PDFs) para análise posterior por modelos de linguagem, especialmente no contexto de processos legais.

**Estrutura Inicial:**
- `src/`: Código fonte principal da aplicação CLI.
  - `input_handler/`: Módulo para carregar arquivos de entrada.
  - `preprocessor/`: Módulo para pré-processar imagens/PDFs (usando Docling, etc.).
  - `extractor/`: Módulo para realizar OCR e extrair informações (usando Langchain/Gemini).
  - `output_handler/`: Módulo para formatar e apresentar os resultados.
  - `main.py`: Ponto de entrada da aplicação CLI.
- `requirements.txt`: Lista de dependências Python do projeto.

**Como Usar:**
*(A ser definido)*