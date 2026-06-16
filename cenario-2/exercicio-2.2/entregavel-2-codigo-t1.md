# Entregável 2 — Código Implementado (T1)

> Implementação da T1 do query endpoint usando GitHub Copilot.
> Todos os arquivos estão no starter repo em
> `Prática 2 - V2/Anexo-D-starter-repo-novatech-assistant/novatech-assistant/`.

---

## Arquivos criados / modificados

### `src/shared/types.ts`

Define os schemas Zod de entrada e saída e os tipos de domínio (tiers, confidence, SearchChunk).

**Decisões de design:**
- `CLIENT_TIERS` como array `as const` → tipo `"Gold" | "Silver" | "Standard"` estrito.
- `MAX_QUESTION_LENGTH = 1_000` e `MAX_HISTORY_TURNS = 3` como constantes exportadas para reuso nos testes.
- `source_document` no `QueryOutputSchema` com `.min(1)` — torna o guardrail VC-02 verificável em tempo de execução.

### `src/shared/config.ts`

Leitura lazy de variáveis de ambiente. Funções retornam strings (não são resolvidas na carga do módulo), evitando que a ausência de env vars quebre os testes unitários.

**Segurança:** nenhuma chave ou endpoint hardcoded. `requireEnv()` lança erro claro se a variável estiver ausente.

### `src/shared/errors.ts`

Hierarquia de erros com `httpStatus` codificado em cada classe. `toErrorResponse()` serializa erros para o cliente **sem** expor stack traces ou cause chain.

### `src/shared/logger.ts`

Instância global de `pino` com:
- `redact` de campos `password`, `apiKey`, `authorization`.
- `isoTime` para compatibilidade com Azure Monitor.
- Nível configurável via `LOG_LEVEL` env var.

### `src/functions/query/validator.ts`

Exporta `parseAndValidateBody(bodyText)` — ponto de entrada do handler — e `validateQueryInput(rawBody)` para testes unitários isolados.

Responsabilidades:
- Parse de JSON com mensagem de erro amigável.
- Validação Zod com mensagens de erro concatenadas.
- Não sanitiza contra prompt injection (documentado na revisão crítica).

### `src/functions/query/handler.ts`

Azure Functions v4 HTTP trigger registrado via `app.http("query", ...)`.

Fluxo T1 (implementado):
1. Gera `requestId` (UUID v4).
2. Parseia e valida body → retorna 400 com `VALIDATION_ERROR` se inválido.
3. Loga questionLength, clientTier e historyTurns (sem logar o conteúdo da pergunta).
4. Stubs marcados com `TODO(T2)` … `TODO(T5)` para tasks seguintes.
5. Retorna 200 com `buildNotFoundResponse()` (stub até T5).

### `src/functions/query/response-builder.ts`

Dois construtores de resposta:
- `buildQueryResponse({ answer, chunks, llmSourceDocument })` — para quando há chunks.
- `buildNotFoundResponse()` — para quando o índice não retorna resultados (VC-04).

Guardrail `source_document` aplicado deterministicamente:
- `buildQueryResponse` lança `AppError('GUARDRAIL_VIOLATION')` se chamado com `chunks = []`.
- `source_document` nunca é `""` — fallback para `topChunk.source_document`.

### `tests/unit/query/validator.test.ts`

22 testes unitários cobrindo:
- Happy paths: question válida, tiers válidos, history válido.
- Sad paths: question vazia/longa, tier inválido, history > 3 turnos, role inválido, JSON malformado, body nulo.

**Resultado:** `22/22 passing` em `vitest run`.

---

## Evidência de execução dos testes

```
 ✓ tests/unit/query/validator.test.ts (22)
   ✓ validateQueryInput (16)
     ✓ question field (7)
     ✓ clientTier field (5)
     ✓ history field (4)
   ✓ parseAndValidateBody (6)

 Test Files  1 passed (1)
      Tests  22 passed (22)
   Duration  36.58s
```
