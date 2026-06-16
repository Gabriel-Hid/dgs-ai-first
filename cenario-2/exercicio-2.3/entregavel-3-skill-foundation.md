# Entregável 3 — SKILL.md Foundation: `error-handling`

> Exercício 2.3 · Skill Foundation principal do NovaTech Assistant
> Esta skill é copiada/referenciada em `skills/foundation/error-handling.md` do starter repo.

---

<!-- Conteúdo abaixo é o SKILL.md completo, pronto para uso pelo agente -->

# skill: error-handling

**Nível:** Foundation  
**Aplica a:** todo arquivo TypeScript do projeto — funções, endpoints, serviços, hooks React.  
**Referenciado por:** `azure-functions-endpoint`, `azure-ai-search-integration`, `testing-patterns`, `create-rag-endpoint`, `create-integration-test`, `react-components`.

---

## 1. Quando aplicar esta skill

Aplique esta skill **sempre que**:
- Gerar ou editar código que faça chamadas a serviços externos (Azure OpenAI, Azure AI Search, Cosmos DB).
- Escrever handlers HTTP (Azure Functions).
- Criar ou modificar qualquer bloco `try/catch`.
- Definir ou lançar erros de domínio.
- Construir respostas HTTP de erro.

---

## 2. Contexto

O projeto usa uma hierarquia de erros tipada com base em `AppError` (`src/shared/errors.ts`).
Todos os erros de domínio **herdam de `AppError`** — nunca de `Error` diretamente.
Respostas HTTP de erro são construídas exclusivamente por `toErrorResponse()`.

Stack traces, mensagens internas e detalhes de causa **nunca chegam ao caller HTTP** — guardrail de segurança.
O logger (`pino`) registra o contexto interno; a resposta ao cliente contém apenas `code` e `message`.

Tipos de erro disponíveis:
| Classe | Código | HTTP Status | Uso |
|---|---|---|---|
| `ValidationError` | `VALIDATION_ERROR` | 400 | Input inválido (falha no schema Zod) |
| `EmbeddingServiceError` | `EMBEDDING_SERVICE_ERROR` | 502 | Falha ao chamar Azure OpenAI embeddings |
| `SearchServiceError` | `SEARCH_SERVICE_ERROR` | 502 | Falha ao chamar Azure AI Search |
| `LlmServiceError` | `LLM_SERVICE_ERROR` | 502 | Falha na geração de resposta pelo LLM |
| `AppError` (direto) | customizável | customizável | Erros de domínio não cobertos pelos anteriores |

---

## 3. Regras Prescritivas

### DEVE

- **DEVE** herdar de `AppError` para todo erro de domínio novo.
- **DEVE** usar `toErrorResponse(error)` para construir a resposta HTTP de erro — nunca montar o JSON manualmente.
- **DEVE** logar o erro com `logger.error({ requestId, err }, 'mensagem')` **antes** de responder ao cliente.
- **DEVE** passar `cause` ao construtor de `AppError` quando o erro envolver uma exceção externa (ex.: erro do SDK Azure).
- **DEVE** verificar `error instanceof AppError` no bloco `catch` do handler para distinguir erros de domínio de erros inesperados.
- **DEVE** retornar `500` para `AppError` genérico / erros desconhecidos e usar o status HTTP da classe para erros tipados.
- **DEVE** capturar erros de validação Zod e convertê-los em `ValidationError` com mensagem legível.

### NÃO DEVE

- **NÃO DEVE** usar `catch (e) {}` silencioso — todo `catch` deve logar ou relançar.
- **NÃO DEVE** retornar `error.stack`, `error.message` do erro original (interno) diretamente na resposta HTTP.
- **NÃO DEVE** usar `throw new Error(...)` fora de `shared/` — use as subclasses de `AppError`.
- **NÃO DEVE** usar `console.log` ou `console.error` — use `logger` (pino) sempre.
- **NÃO DEVE** incluir dados de PII ou payload de request no log de erro — logar apenas `requestId` e o código de erro.
- **NÃO DEVE** criar subclasse de `AppError` sem código semântico (ex.: `"ERROR"` genérico não é aceitável).
- **NÃO DEVE** usar `any` no tipo do parâmetro `catch` — prefira `unknown` e faça narrowing.

---

## 4. Exemplos DO / DON'T

### 4.1 Handler HTTP — tratamento de erro

**✅ DO — correto**
```typescript
import { app, HttpRequest, HttpResponseInit, InvocationContext } from "@azure/functions";
import { logger } from "../shared/logger.js";
import { toErrorResponse, ValidationError, AppError } from "../shared/errors.js";
import { QueryInputSchema } from "../shared/types.js";
import { randomUUID } from "node:crypto";

export async function queryHandler(
  req: HttpRequest,
  context: InvocationContext
): Promise<HttpResponseInit> {
  const requestId = randomUUID();

  // 1. Validação de input com Zod — lança ValidationError em caso de falha
  const parseResult = QueryInputSchema.safeParse(await req.json());
  if (!parseResult.success) {
    const message = parseResult.error.errors.map((e) => e.message).join("; ");
    throw new ValidationError(message);
  }

  try {
    // 2. Lógica de domínio (pode lançar AppError tipados)
    const result = await runQueryPipeline(parseResult.data, requestId);
    return { status: 200, jsonBody: result };
  } catch (err: unknown) {
    // 3. Erro tipado: logar internamente, responder com toErrorResponse
    if (err instanceof AppError) {
      logger.error({ requestId, code: err.code, err }, "Domain error in queryHandler");
      return { status: err.httpStatus, jsonBody: toErrorResponse(err) };
    }
    // 4. Erro inesperado: nunca vazar detalhes
    logger.error({ requestId, err }, "Unexpected error in queryHandler");
    return { status: 500, jsonBody: toErrorResponse(err) };
  }
}
```

**❌ DON'T — incorreto**
```typescript
// ❌ catch silencioso — erro engolido, nenhum log, resposta 200 com undefined
export async function queryHandler(req: HttpRequest): Promise<HttpResponseInit> {
  try {
    const body = await req.json();
    const result = await runQueryPipeline(body as any); // ❌ any
    return { status: 200, jsonBody: result };
  } catch (e) {} // ❌ catch silencioso

  return { status: 200, jsonBody: {} }; // ❌ resposta vazia sem indicar erro
}

// ❌ vazamento de stack trace para o caller
export async function badHandler(req: HttpRequest): Promise<HttpResponseInit> {
  try {
    const result = await runQueryPipeline(await req.json() as any);
    return { status: 200, jsonBody: result };
  } catch (e: any) { // ❌ any no catch
    console.error(e); // ❌ console.error em vez de pino logger
    return {
      status: 500,
      jsonBody: { error: e.message, stack: e.stack }, // ❌ stack trace exposto
    };
  }
}
```

---

### 4.2 Erro de serviço externo — wrap correto

**✅ DO — correto**
```typescript
import { SearchServiceError } from "../shared/errors.js";
import { logger } from "../shared/logger.js";
import type { SearchChunk } from "../shared/types.js";

export async function searchChunks(
  embedding: number[],
  requestId: string
): Promise<SearchChunk[]> {
  try {
    const response = await azureSearchClient.search(embedding);
    return response.results.map(mapToSearchChunk);
  } catch (err: unknown) {
    // Wrapa o erro do SDK em SearchServiceError — causa preservada para debug interno
    logger.error({ requestId, err }, "Azure AI Search call failed");
    throw new SearchServiceError(
      "Failed to retrieve search results",
      err // cause preservado internamente
    );
  }
}
```

**❌ DON'T — incorreto**
```typescript
export async function searchChunks(embedding: number[]): Promise<any> { // ❌ retorno any
  try {
    return await azureSearchClient.search(embedding);
  } catch (err) {
    throw new Error(`Search failed: ${err}`); // ❌ Error nativo, sem código semântico
  }
}
```

---

### 4.3 Validação de input Zod → ValidationError

**✅ DO — correto**
```typescript
import { z } from "zod";
import { ValidationError } from "../shared/errors.js";

export function parseQueryInput(raw: unknown) {
  const result = QueryInputSchema.safeParse(raw);
  if (!result.success) {
    const message = result.error.errors
      .map((issue) => `${issue.path.join(".")}: ${issue.message}`)
      .join("; ");
    throw new ValidationError(message);
  }
  return result.data;
}
```

**❌ DON'T — incorreto**
```typescript
export function parseQueryInput(raw: any) { // ❌ any
  // ❌ parse direto — lança ZodError genérico sem código semântico
  return QueryInputSchema.parse(raw);
}
```

---

### 4.4 Log de erro — sem PII

**✅ DO — correto**
```typescript
// ✅ Loga requestId e código de erro — sem payload, sem PII
logger.error({ requestId, code: err.code, httpStatus: err.httpStatus }, "Query pipeline failed");
```

**❌ DON'T — incorreto**
```typescript
// ❌ Loga o body da request — pode conter PII do cliente (nome, email, dados pessoais)
logger.error({ requestId, body: requestBody, err }, "Query pipeline failed");

// ❌ console.log — bypassa o pino (sem redact, sem structured logging)
console.error("Error:", err);
```

---

## 5. Anti-Padrões (armadilhas reais do Copilot sem esta skill)

| Anti-Padrão | Por que é problema | Correção |
|---|---|---|
| `catch (e) {}` silencioso | Erro engolido, impossível diagnosticar em produção | Sempre logar ou relançar |
| `throw new Error("msg")` fora de `shared/` | Sem código semântico; handler não sabe o status HTTP | Usar `ValidationError`, `LlmServiceError` etc. |
| `catch (e: any)` | Perde type-safety; oculta o tipo real | `catch (err: unknown)` + narrowing com `instanceof` |
| `console.error(err)` | Bypassa pino (sem redact PII, sem structured JSON) | `logger.error({ requestId, err }, 'msg')` |
| `jsonBody: { error: e.message, stack: e.stack }` | Vaza internals para o cliente — OWASP A05 | `toErrorResponse(err)` — nunca expõe stack |
| `return { status: 200, jsonBody: {} }` após erro | Status 200 mascara falha; cliente não sabe que houve erro | Retornar status HTTP correto via `err.httpStatus` |
| Log do payload completo | Pode conter PII (nome de cliente, pergunta sensível) | Logar apenas `requestId` e metadados de contexto |
| Novo `AppError` sem código semântico (`"ERROR"`) | Impossível filtrar/alertar por tipo de erro no Azure Monitor | Sempre definir código string descritivo (`"PAYMENT_ERROR"` etc.) |
| `toErrorResponse(err, true)` em produção | `includeDetails: true` expõe `cause` para o caller | Usar `includeDetails` apenas em ambientes de dev/teste internos |

---

## 6. Referências Internas

- Implementação de referência: [`src/shared/errors.ts`](../../Prática%202%20-%20V2/Anexo-D-starter-repo-novatech-assistant/novatech-assistant/src/shared/errors.ts)
- Logger configurado: [`src/shared/logger.ts`](../../Prática%202%20-%20V2/Anexo-D-starter-repo-novatech-assistant/novatech-assistant/src/shared/logger.ts)
- Tipos de domínio: [`src/shared/types.ts`](../../Prática%202%20-%20V2/Anexo-D-starter-repo-novatech-assistant/novatech-assistant/src/shared/types.ts)
- Skills que referenciam esta: `azure-functions-endpoint`, `azure-ai-search-integration`, `testing-patterns`, `create-rag-endpoint`, `create-integration-test`
