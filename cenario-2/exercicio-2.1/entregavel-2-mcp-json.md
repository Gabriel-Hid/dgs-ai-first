# Entregável 2 — `.mcp/mcp.json` final + justificativa de escopo

> Exercício 2.1 · Voltar ao [índice](README.md)

Arquivo: [.mcp/mcp.json](../../Prática%202%20-%20V2/Anexo-D-starter-repo-novatech-assistant/novatech-assistant/.mcp/mcp.json)

## Justificativa por server (least privilege concreto)

- **`filesystem-dev`** → `./src ./specs ./skills ./prompts`: é o **único** server com escrita.
  Recebe só as pastas onde o dev/agente produz artefatos. Não inclui `docs/`, `data/`,
  `infra/` nem a raiz — o agente não tem por que escrever lá.
- **`filesystem-docs-novatech`** → `./docs/novatech`: fonte de verdade normativa. Server
  **separado** para isolar o escopo; deve ser tratado como read-only (ver enforcement abaixo).
- **`filesystem-retrieval-corpus`** → `./data/retrieval-corpus`: output do pipeline de RAG.
  Server **separado** read-only — o agente de query só lê.
- **`git`** → `--repository .`: dá histórico/diff/branches sem precisar de GitHub. As tools de
  escrita (`git_commit`, `git_checkout`…) existem no server, mas o uso é restrito a leitura
  (ver enforcement). Mudanças passam pelo dev.
- **`memory`** → grafo local: acumula linguagem ubíqua e decisões. Não recebe segredos.
- **`everything`** → sandbox de aprendizado das primitivas; **será removido** após o onboarding.

## Enforcement de read-only — limitação honesta e mitigação
O `@modelcontextprotocol/server-filesystem` rodado por **`npx` não tem flag `ro` por
diretório** — ele expõe `write_file`/`edit_file`/`move_file`/`create_directory` para todos os
diretórios permitidos. O read-only de `docs/novatech` e `data/retrieval-corpus` é obtido por
**3 camadas**:
1. **Segregação de escopo** — servers distintos por fonte (já no `mcp.json`). Limita o
   *blast radius*: cada server só enxerga sua pasta.
2. **Permissão de ferramentas no cliente** — desabilitar as tools de escrita
   (`write_file`, `edit_file`, `move_file`, `create_directory`) para as instâncias
   `filesystem-docs-novatech` e `filesystem-retrieval-corpus`, e as tools de escrita do `git`
   (allow-list só com `git_log`, `git_status`, `git_diff*`, `git_show`, `git_branch`).
3. **Git como validation gate** — qualquer escrita indevida aparece em `git diff` e é barrada
   no code review antes de virar commit.
4. *(Alternativa endurecida)* mount **Docker** com sufixo `:ro` faz o próprio server recusar
   escrita no SO — opção para ambientes que exijam enforcement forte sem confiar no cliente.
