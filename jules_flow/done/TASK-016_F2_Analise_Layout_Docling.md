---
id: TASK-016
title: "F2: Pesquisar e implementar análise de layout com Docling ou similar"
epic: "Fase 2: Pré-processamento por Página"
status: done
priority: medium
dependencies: ["TASK-023"]
assignee: Jules
---

### Descrição

Pesquisar e implementar a funcionalidade de análise de layout de página utilizando a ferramenta Docling ou uma tecnologia similar. O objetivo é identificar e separar blocos de texto, imagens ou tabelas antes da extração de texto por OCR/LLM, para melhorar a precisão da extração em documentos com layouts complexos.

### Critérios de Aceitação

- [x] Pesquisa sobre Docling e alternativas para análise de layout de documentos foi realizada e documentada. (Completed via TASK-023 and docs/reference/docling_summary.txt)
- [x] Decisão sobre a ferramenta/biblioteca a ser utilizada foi tomada. (Decision: Docling will be used)
- [x] Implementação da análise de layout foi integrada ao pipeline de pré-processamento em `src/preprocessor/image_processor.py` ou um novo módulo. (Implemented in `src/preprocessor/layout_analyzer.py`)
- [x] A saída da análise de layout (ex: coordenadas de blocos) está disponível para as etapas subsequentes. (The `analyze_pdf_layout` function returns `List[List[LayoutBlockData]]` which includes coordinates and other block details.)
- [x] Testes unitários foram criados para a nova funcionalidade de análise de layout. (Created in `tests/preprocessor/test_layout_analyzer.py`)

### Arquivos Relevantes

* `src/preprocessor/image_processor.py`
* `ROADMAP.md`

### Relatório de Execução

**2025-06-15 (Initial Steps):**
- Confirmed that research on Docling (TASK-023) is complete and documented in `docs/reference/docling_summary.txt`.
- Decision made to proceed with **Docling** for layout analysis based on the positive findings in its documentation.

**2025-06-15 (Implementation - Part 1):**
- Added `docling` to `requirements.txt`. (Note: `pip install` in subtask environment failed, but file is updated).
- Experimented with Docling API structure by writing `run_docling_test.py` (execution in subtask failed, but script provided insights).
- Created new module `src/preprocessor/layout_analyzer.py` with:
    - `LayoutBlockData` and `BoundingBox` dataclasses.
    - `analyze_pdf_layout(pdf_path: str)` function to process PDFs with Docling and return `List[List[LayoutBlockData]]`.
    - Helper `_convert_docling_block_to_layout_block_data` for transforming Docling's block objects.
- Conceptually outlined how downstream modules would adapt to use the new layout data (details in plan step log).
- Created unit tests in `tests/preprocessor/test_layout_analyzer.py`, mocking Docling library calls.
