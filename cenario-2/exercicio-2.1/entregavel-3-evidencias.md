# Entregável 3 — Evidência de uso real (via protocolo MCP)

> Exercício 2.1 · Voltar ao [índice](README.md)

A evidência foi coletada falando **JSON-RPC stdio** diretamente com cada server (handshake
`initialize` → `tools/list` → `tools/call`), o mesmo protocolo que o agente Claude/Copilot usa
ao carregar o `.mcp/mcp.json`. Os servers sobem via os comandos exatos do `mcp.json`.

## (a) Ler documentação de negócio — `filesystem-docs-novatech`
```
INIT serverInfo: {"name":"secure-filesystem-server","version":"0.2.0"}
[server] Client does not support MCP Roots, using allowed directories set from server args:
  [ ...\novatech-assistant\docs\novatech ]
TOOLS: read_file, read_text_file, ..., list_directory, search_files, list_allowed_directories

CALL list_directory {"path":"./docs/novatech"} =>
[FILE] FAQ-atendimento.md
[FILE] POL-001-politica-devolucao.md
[FILE] PROC-042-frete-especial-v1.md
[FILE] PROC-042-v2-frete-especial-revisado.md
[FILE] README.md
[FILE] SLA-2024-tabela-sla-clientes.md

CALL read_text_file {"path":"./docs/novatech/POL-001-politica-devolucao.md","head":15} =>
# POL-001 — Política de Devolução de Mercadorias
**Versão:** 3.1
...
```
**Prova de least privilege** — tentativa de ler fora do escopo foi **negada**:
```
CALL read_text_file {"path":"./package.json"} =>
Access denied - path outside allowed directories:
  ...\novatech-assistant\package.json not in ...\novatech-assistant\docs\novatech
```

## (b) Recuperar chunk do corpus — `filesystem-retrieval-corpus`
Pergunta do gabarito (Anexo B): **"Posso devolver carga perigosa?" → deve recuperar POL-001-B.**
```
INIT serverInfo: {"name":"secure-filesystem-server","version":"0.2.0"}
CALL list_directory {"path":"./data/retrieval-corpus"} =>
[FILE] chunks-novatech.md
[FILE] README.md

(recuperado de chunks-novatech.md)
**Chunk POL-001-B** — Seção 3.2: Exceções
> As seguintes categorias de carga NÃO são elegíveis para devolução pelo processo padrão:
> Cargas perigosas classificadas nas classes 1 a 6 da ANTT ... o cliente deve entrar em
> contato com o setor de Gestão de Riscos (ramal 4500) para tratamento individual.
```
O mapa de cobertura do próprio corpus confirma o gabarito:
`| "Posso devolver carga perigosa?" | POL-001-B | FAQ-03, POL-001-A |`.

## (c) Ler histórico do repositório — `git`
```
INIT serverInfo: {"name":"mcp-git","version":"1.27.2"}
TOOLS: git_status, git_diff_unstaged, git_diff_staged, git_diff, git_commit, git_add,
       git_reset, git_log, git_create_branch, git_checkout, git_show, git_branch

CALL git_log {"repo_path":".","max_count":5} =>
Commit: 'bbdd03aeecd7e349a2bfc93849e0552a0b766ac6'
Author: Trilha AI First <trilha@db1.local>
Date: 2026-06-09 ...
Message: 'chore: starter repo (Anexo D) — estrutura + dados semeados dos Anexos A e B'

CALL git_status {"repo_path":"."} =>
On branch master
Changes not staged for commit:
        modified:   .mcp/mcp.json
```

> Reprodutibilidade: a coleta usou um probe MCP stdio (`initialize`/`tools/list`/`tools/call`)
> com os mesmos comandos do `mcp.json`. Em uso normal, basta abrir o Claude/Copilot com o
> `.mcp/mcp.json` carregado; o agente executa essas mesmas chamadas.
