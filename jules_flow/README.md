# Jules-Flow System README

## Propósito do Sistema

Jules-Flow é um sistema de gerenciamento de microtarefas projetado para ser operado pelo agente de IA, Jules, sob a supervisão de um Desenvolvedor humano. O sistema é inteiramente baseado em arquivos Markdown e visa estruturar e rastrear o trabalho de desenvolvimento realizado por Jules.

## Fluxo do Sistema

O fluxo de trabalho no Jules-Flow é centrado em arquivos Markdown que representam tarefas individuais. O processo geral é o seguinte:

1.  **Geração de Tarefas**:
    *   Tarefas podem ser geradas de duas formas:
        *   A partir da análise do `ROADMAP.md` principal do projeto.
        *   Através de solicitações diretas do Desenvolvedor para tarefas não planejadas no roadmap.
    *   Para tarefas do roadmap, Jules analisa os épicos e objetivos descritos. Para demandas diretas, Jules utiliza as informações fornecidas pelo Desenvolvedor.
    *   Para cada microtarefa identificada, um novo arquivo `.md` é criado na pasta `/jules_flow/backlog/` usando o `/jules_flow/templates/task_template.md`.
    *   O frontmatter YAML do arquivo da tarefa é preenchido com `id`, `title`, `epic`, e o `status` inicial é definido como `backlog`.

2.  **Execução de Tarefas**:
    *   Jules seleciona uma tarefa da pasta `/jules_flow/backlog/`.
    *   As alterações de código necessárias para completar a tarefa são realizadas no branch `jules`.
    *   Após a conclusão do código e a verificação dos critérios de aceitação, Jules preenche a seção "Relatório de Execução" no arquivo da tarefa.
    *   O `status` no frontmatter do arquivo da tarefa é atualizado para `done`.

3.  **Relatório e Conclusão**:
    *   O arquivo `/jules_flow/TASK_INDEX.md` é atualizado para refletir o novo status da tarefa.
    *   O `ROADMAP.md` é atualizado, marcando o item correspondente à tarefa como concluído (✅).
    *   Um commit atômico é feito no branch `jules`, incluindo todas as alterações de código, o arquivo da tarefa atualizado, o `TASK_INDEX.md` atualizado e o `ROADMAP.md` atualizado.
    *   O arquivo da tarefa é movido da pasta `/jules_flow/backlog/` para `/jules_flow/done/`.

## Estrutura de Pastas

*   `/jules_flow/`: Diretório raiz do sistema Jules-Flow.
    *   `/backlog/`: Contém tarefas pendentes (arquivos `.md`).
    *   `/done/`: Contém tarefas concluídas (arquivos `.md`).
    *   `/templates/`: Contém o modelo `task_template.md` para novas tarefas.
    *   `README.md`: Este arquivo.
    *   `INSTRUCTIONS_FOR_JULES.md`: Instruções operacionais para o agente Jules.
    *   `TASK_INDEX.md`: Índice e relatório de progresso de todas as tarefas.

Este sistema permite um gerenciamento de projetos transparente e eficiente, com todo o histórico e progresso documentado em Markdown.
