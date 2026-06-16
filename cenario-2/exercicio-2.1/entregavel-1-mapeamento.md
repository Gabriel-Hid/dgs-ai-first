# Entregável 1 — Mapeamento: necessidade → server

> Exercício 2.1 · Voltar ao [índice](README.md)

| Necessidade do projeto | Server (escopo) | Primitivas expostas | Consumidor | Acesso |
|---|---|---|---|---|
| Ler/editar código, specs, skills, prompts | `filesystem-dev` → `./src ./specs ./skills ./prompts` | **Tools**: `read_text_file`, `write_file`, `edit_file`, `create_directory`, `move_file`, `list_directory`, `search_files`, `directory_tree`, `get_file_info` · **Resources**: arquivos das pastas · **Prompts**: — | Dev + agente (Copilot/Claude) durante implementação (2.2/2.3) | **read-write** |
| Ler documentação de negócio NovaTech | `filesystem-docs-novatech` → `./docs/novatech` | mesmas tools do filesystem (mas só leitura deve ser usada) · **Resources**: POL-001, PROC-042 v1/v2, SLA-2024, FAQ | Agente de query / autor de specs | **read-only** (intenção) |
| "Recuperar" chunks do RAG | `filesystem-retrieval-corpus` → `./data/retrieval-corpus` | idem · **Resources**: `chunks-novatech.md` | Agente de query (simula Azure AI Search) | **read-only** (intenção) |
| Histórico / diff / branches do repo | `git` → `--repository .` | **Tools**: `git_log`, `git_status`, `git_diff`, `git_diff_unstaged`, `git_diff_staged`, `git_show`, `git_branch` (leitura) · `git_commit`, `git_add`, `git_reset`, `git_create_branch`, `git_checkout` (escrita) | Dev + agente para inspecionar histórico | **leitura** (escrita restrita no cliente) |
| Memória persistente (linguagem ubíqua, decisões) | `memory` → grafo local | **Tools**: `create_entities`, `create_relations`, `add_observations`, `read_graph`, `search_nodes` | Agente entre sessões | **read-write** (sem segredos) |
| Aprender as primitivas MCP | `everything` → sandbox | Tools/Resources/Prompts de exemplo | Dev (onboarding) | sandbox — **remover após onboarding** |

## Pastas que NÃO entram em nenhum escopo (decisão explícita)
- **Raiz do repositório** (`./`) — evita expor tudo de uma vez.
- **`.env`** e quaisquer arquivos de segredo.
- **`infra/parameters/`** (`dev.bicepparam`, `staging.bicepparam`, `prod.bicepparam`) — podem conter nomes de recursos/segredos de ambiente.
- **`.git/`** internamente (acessado só via server `git`, não via filesystem).
