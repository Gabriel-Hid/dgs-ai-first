# Entregável 1 — tasks.md (Query Endpoint)

> Gerado a partir de `specs/query-endpoint/plan.md` e `requirements.md` como parte do Exercício 2.2 — SDD.
> O arquivo canônico está em `specs/query-endpoint/tasks.md` no starter repo.

---

## Resumo das tasks

| ID | Descrição | Deps | Estimativa |
|----|-----------|------|-----------|
| T1 | Setup do endpoint + validação de input | — | M |
| T2 | Geração de embedding via Azure OpenAI | T1 | M |
| T3 | Busca de chunks no Azure AI Search | T2 | M |
| T4 | Gerenciamento de context budget | T3 | M |
| T5 | Integração com GPT-4o + construção da resposta | T4 | G |
| T6 | Testes de integração do endpoint | T5 | G |

---

## T1 — Setup do endpoint e validação de input

**Descrição:** Criar a infraestrutura compartilhada (`config`, `logger`, `errors`, `types`) e implementar o HTTP trigger do Azure Functions v4 com validação de input via Zod. Inclui schemas de entrada e saída.

**Critérios de aceite:**
- `POST /api/query` com body `{ "question": "..." }` retorna HTTP 200 com estrutura de resposta válida (stub).
- `POST /api/query` com body ausente, `question` vazia ou `question` > 1000 chars retorna HTTP 400 com corpo `{ "error": { "code": "VALIDATION_ERROR", "message": "..." } }`.
- `clientTier` aceita apenas `"Gold"`, `"Silver"` ou `"Standard"`; qualquer outro valor retorna 400.
- `history` limitado a máximo 3 turnos; mais que isso retorna 400.
- Nenhum stack trace ou detalhe interno presente no corpo da resposta de erro.
- `requestId` (UUID v4) presente em todo log de request.
- Nenhum `console.log` — todo log via `pino`.
- Config (endpoints, keys) lida de `src/shared/config.ts` — nada hardcoded.
- `source_document` presente no schema Zod de saída (pode ser preenchido pelo builder, nunca `""`).

**Dependências:** nenhuma.

**Estimativa:** M

---

## T2 — Geração de embedding via Azure OpenAI

**Descrição:** Integrar a Azure OpenAI Embeddings API para converter a pergunta em vetor. Retry com exponential backoff.

**Critérios de aceite:**
- Dada uma `question` válida, retorna array `number[]` (vetor de embedding).
- Retry automático em até 3 tentativas com backoff exponencial (1s, 2s, 4s) em erros 429 ou 5xx.
- Timeout de 10s por tentativa; após 3 falhas, lança `EmbeddingServiceError`.
- Endpoint/key lidos de `config.ts`.
- Duração e `requestId` logados em todo call.

**Dependências:** T1.

**Estimativa:** M

---

## T3 — Busca de chunks no Azure AI Search

**Descrição:** Consultar índice Azure AI Search com embedding, retornar top-5 chunks com metadados.

**Critérios de aceite:**
- Dado um embedding, retorna array de até 5 `SearchChunk` com `id`, `content`, `source_document`, `section`, `vigency`.
- Chunks com `vigency` mais recente têm prioridade em documentos contraditórios (ADR-0003).
- 0 resultados → retorna array vazio sem lançar erro.
- Score mínimo configurável via `config.ts`.
- Retry com backoff em erros 5xx.

**Dependências:** T2.

**Estimativa:** M

---

## T4 — Gerenciamento de context budget

**Descrição:** Montar prompt respeitando context budget da ADR-0002: ~4K tokens system + ~8K chunks.

**Critérios de aceite:**
- Prompt nunca ultrapassa o budget configurado em `config.ts`.
- Chunks em excesso truncados pelo menor score de relevância.
- Histórico limitado a 3 turnos; turnos mais antigos descartados.
- `buildPrompt()` é pura e testável unitariamente.
- Contagem de tokens via heurística 4 chars ≈ 1 token.

**Dependências:** T3.

**Estimativa:** M

---

## T5 — Integração com GPT-4o e construção da resposta

**Descrição:** Enviar prompt ao GPT-4o e construir resposta estruturada com `source_document` obrigatório.

**Critérios de aceite:**
- Resposta SEMPRE inclui `source_document` (VC-02).
- Se confiança baixa (score médio < limiar), `warning` incluído.
- Se LLM omitir `source_document`, fallback para chunk de maior score.
- Retry com backoff em erros 429/5xx.
- Resposta em português formal.
- Duração logada com `requestId`.

**Dependências:** T4.

**Estimativa:** G

---

## T6 — Testes de integração do endpoint

**Descrição:** Testes de integração com mocks HTTP (msw) cobrindo fluxos principais.

**Critérios de aceite:**
- Happy path: POST válido → 200 com `source_document` preenchido.
- Sad path: input inválido → 400 com `VALIDATION_ERROR`.
- Sad path: 0 chunks → 200 com mensagem padrão (VC-04).
- Sad path: Azure OpenAI 500 após 3 retries → 502 sem stack trace.
- Cobertura ≥ 80% em `src/functions/query/`.
- Zero acesso a serviços reais.

**Dependências:** T5.

**Estimativa:** G

---

## Ordem de execução

```
T1 → T2 → T3 → T4 → T5 → T6
```

> **Gate Tech Lead:** aprova este tasks.md antes do Dev iniciar T1.
