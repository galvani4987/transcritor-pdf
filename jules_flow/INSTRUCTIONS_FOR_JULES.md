# Instruções Operacionais para Jules (Jules-Flow)

Este documento detalha as regras e procedimentos que eu, Jules, devo seguir ao operar o sistema de gerenciamento de tarefas Jules-Flow.

## Princípios Gerais

1.  **Automação e Precisão**: Minha principal função é automatizar o gerenciamento de tarefas. Devo ser preciso e consistente na aplicação das regras.
2.  **Comunicação Clara**: Devo comunicar o status das tarefas e quaisquer problemas de forma clara ao Desenvolvedor.
3.  **Adesão ao Fluxo**: Devo seguir rigorosamente o fluxo de trabalho definido para geração, execução e relatório de tarefas.
4.  **Branch `jules`**: Todo o trabalho de codificação e atualização de arquivos de tarefas deve ser feito no branch `jules`.

## Funcionalidade 1: Geração de Tarefas a partir do Roadmap

Processo:

1.  **Análise do `ROADMAP.md`**:
    *   Ler uma "Fase" específica do `ROADMAP.md` conforme instruído pelo Desenvolvedor.
    *   Identificar tarefas de alto nível dentro dessa fase.

2.  **Criação de Arquivos de Tarefa**:
    *   Para cada tarefa de alto nível, criar um novo arquivo `.md` na pasta `/jules_flow/backlog/`.
    *   Utilizar `/jules_flow/templates/task_template.md` como base.
    *   Preencher o frontmatter YAML:
        *   `id`: Gerar um ID sequencial único (ex: `TASK-001`, `TASK-002`). Consultar `TASK_INDEX.md` ou a pasta `backlog/` e `done/` para determinar o próximo ID disponível.
        *   `title`: Criar um título curto e descritivo para a tarefa.
        *   `epic`: Copiar o nome da "Fase" ou Épico do `ROADMAP.md`.
        *   `status`: Definir inicialmente como `backlog`.
        *   `priority`: Definir inicialmente como `medium` (pode ser ajustado pelo Desenvolvedor posteriormente).
        *   `dependencies`: Listar IDs de tarefas das quais esta tarefa depende (se aplicável, inicialmente pode ser vazio).
        *   `assignee`: Definir como `Jules`.
    *   Gerar uma "Descrição" detalhada do objetivo da tarefa com base no `ROADMAP.md`.
    *   Gerar "Critérios de Aceitação" claros e testáveis.
    *   Listar "Arquivos Relevantes" se puderem ser inferidos (caso contrário, deixar em branco).
    *   A seção "Relatório de Execução" deve ser deixada em branco.

3.  **Atualização do `TASK_INDEX.md`**:
    *   Adicionar uma nova linha na tabela do `TASK_INDEX.md` para a nova tarefa, incluindo `ID`, `Título da Tarefa`, `Status` (`backlog`) e `Epic`.

### Geração de Tarefas por Demanda do Desenvolvedor

Este processo descreve como criar tarefas diretamente a partir de solicitações do Desenvolvedor, que podem não estar detalhadas no `ROADMAP.md`.

Processo:

1.  **Recebimento da Solicitação**:
    *   O Desenvolvedor fornecerá os detalhes da tarefa, incluindo uma descrição, objetivos e, se possível, critérios de aceitação.

2.  **Criação de Arquivos de Tarefa**:
    *   Criar um novo arquivo `.md` na pasta `/jules_flow/backlog/`.
    *   Utilizar `/jules_flow/templates/task_template.md` como base.
    *   Preencher o frontmatter YAML:
        *   `id`: Gerar um ID sequencial único (ex: `TASK-001`, `TASK-002`). Consultar `TASK_INDEX.md` ou as pastas `backlog/` e `done/` para determinar o próximo ID disponível.
        *   `title`: Criar um título curto e descritivo para a tarefa, conforme fornecido ou inferido da solicitação.
        *   `epic`: Definir como "Demanda Direta" ou utilizar um valor de épico fornecido pelo Desenvolvedor. Se não especificado, usar "Demanda Direta".
        *   `status`: Definir inicialmente como `backlog`.
        *   `priority`: Definir inicialmente como `medium` (ou conforme especificado pelo Desenvolvedor).
        *   `dependencies`: Listar IDs de tarefas das quais esta tarefa depende (se aplicável, conforme especificado pelo Desenvolvedor).
        *   `assignee`: Definir como `Jules`.
    *   Gerar uma "Descrição" detalhada com base na solicitação do Desenvolvedor.
    *   Gerar "Critérios de Aceitação" claros e testáveis com base na solicitação.
    *   Listar "Arquivos Relevantes" se puderem ser inferidos ou forem fornecidos.
    *   A seção "Relatório de Execução" deve ser deixada em branco.

3.  **Atualização do `TASK_INDEX.md`**:
    *   Adicionar uma nova linha na tabela do `TASK_INDEX.md` para a nova tarefa, incluindo `ID`, `Título da Tarefa`, `Status` (`backlog`) e `Epic`.

## Funcionalidade 2: Execução e Relatório de Tarefas

Processo:

1.  **Seleção e Leitura da Tarefa**:
    *   Identificar e analisar o conteúdo de um arquivo de tarefa `.md` da pasta `/jules_flow/backlog/`, geralmente a tarefa com maior prioridade ou a próxima na sequência lógica.

2.  **Execução do Código**:
    *   Realizar todas as alterações de código necessárias no branch `jules` para cumprir os "Critérios de Aceitação" da tarefa.
    *   Testar as alterações (adicionar testes unitários, se aplicável).

3.  **Preenchimento do Relatório de Execução**:
    *   Após a conclusão do código, editar o arquivo da tarefa `.md`.
    *   Preencher a seção "Relatório de Execução" com um resumo das alterações feitas, como foram testadas e quaisquer observações relevantes.

4.  **Atualização de Status (Arquivo da Tarefa)**:
    *   Alterar o valor do campo `status` no frontmatter do arquivo da tarefa para `done`.

5.  **Atualização do `TASK_INDEX.md`**:
    *   Ler o arquivo `TASK_INDEX.md`.
    *   Encontrar a linha correspondente ao `id` da tarefa.
    *   Atualizar o `Status` para `done`.

6.  **Atualização do `ROADMAP.md`**:
    *   Editar o `ROADMAP.md`.
    *   Marcar o item correspondente à tarefa concluída com um ✅.

7.  **Commit Atômico**:
    *   Realizar um único commit no branch `jules`.
    *   O commit deve incluir:
        *   Todas as alterações de código.
        *   O arquivo da tarefa `.md` atualizado (com o relatório e status `done`).
        *   O arquivo `TASK_INDEX.md` atualizado.
        *   O arquivo `ROADMAP.md` atualizado.
    *   A mensagem de commit deve ser clara e referenciar o ID da tarefa (ex: "Completa TASK-001: Implementar funcionalidade X").

8.  **Movimentação de Arquivo**:
    *   Mover o arquivo da tarefa `.md` da pasta `/jules_flow/backlog/` para `/jules_flow/done/`.

## Manutenção do Sistema

*   Manter o `TASK_INDEX.md` sempre atualizado.
*   Garantir que os IDs das tarefas sejam únicos e sequenciais.
*   Em caso de erro ou necessidade de rollback, comunicar ao Desenvolvedor.
