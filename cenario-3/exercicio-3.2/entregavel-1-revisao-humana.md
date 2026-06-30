# Entregável 1 — Revisão Humana do feedback-handler.ts

> Exercício 3.2 · Revisão Crítica de Outputs de IA · Desenvolvedor
> **Esta revisão foi feita ANTES de usar qualquer ferramenta de IA** — disciplina obrigatória do exercício.

---

## Código Revisado

```typescript
// feedback-handler.ts — gerado pelo Copilot
import { app, HttpRequest, HttpResponseInit } from '@azure/functions';

export async function feedbackHandler(
  request: HttpRequest
): Promise<HttpResponseInit> {
  const body = await request.json() as any;                    // ← linha 7

  const feedback = {
    queryId: body.queryId,
    rating: body.rating,
    comment: body.comment,
    attendantEmail: body.attendantEmail,                       // ← linha 14
    timestamp: new Date().toISOString()
  };

  console.log('Feedback recebido:', JSON.stringify(feedback)); // ← linha 17

  const { CosmosClient } = require('@azure/cosmos');           // ← linha 19
  const client = new CosmosClient(process.env.COSMOS_CONNECTION_STRING); // ← linha 20
  const database = client.database('novatech');
  const container = database.container('feedbacks');

  await container.items.create(feedback);                      // ← linha 24

  return { status: 200, body: 'OK' };                         // ← linha 26
}
```

---

## Problemas Identificados

### Problema R-1: `as any` sem validação Zod — body tratado como estrutura confiável

**Trecho:** `const body = await request.json() as any;`

**Categoria:** Violação de AGENTS.md + Problema de segurança

**Descrição detalhada:**

O body da requisição HTTP é dado externo não confiável. Ao fazer `as any`, o TypeScript silencia qualquer erro de tipo e o código passa a tratar `body.queryId`, `body.rating` e `body.comment` como se existissem e fossem dos tipos corretos — sem nenhuma garantia.

**Consequências concretas:**
- `body.queryId` pode ser `undefined` → documento criado no Cosmos DB sem `queryId`, corrompendo a base de dados.
- `body.rating` pode ser string `"5"` (texto) em vez de número `5` → falha silenciosa na lógica de cálculo de médias downstream.
- `body.rating` pode ser `-999` ou `9999` → valor inválido persistido sem rejeição.
- Um atacante pode enviar um body com campos extras (`__proto__`, `constructor`) que nem deveriam existir.

**AGENTS.md:** "Zod para validação de input" — explícito e não negociável.

---

### Problema R-2: `console.log` em vez de `pino`

**Trecho:** `console.log('Feedback recebido:', JSON.stringify(feedback));`

**Categoria:** Violação de AGENTS.md

**Descrição detalhada:**

AGENTS.md é explícito: "pino para logging (nunca console.log)". O `console.log`:
- Não tem structured logging (JSON) — impede indexação e busca no Azure Monitor.
- Não tem redação automática de campos sensíveis (`password`, `apiKey`, `authorization`).
- Não tem nível de log configurável (`debug`/`info`/`warn`/`error`) — tudo vai para stdout indistintamente.
- Não carrega `requestId` nem contexto de trace — impossível correlacionar o log com a requisição.

**Impacto secundário:** Como o `feedback` objeto é serializado completo (próximo problema), `console.log` é o veículo pelo qual o PII vaza para os logs.

---

### Problema R-3: `attendantEmail` logado — dado pessoal em log persistente

**Trecho:** `JSON.stringify(feedback)` onde `feedback` inclui `attendantEmail: body.attendantEmail`

**Categoria:** Problema de segurança (OWASP A02 — Cryptographic Failures / exposição de PII)

**Descrição detalhada:**

O e-mail do atendente é um dado pessoal (PII) protegido pela LGPD. Ao serializar o objeto `feedback` completo com `JSON.stringify` e passá-lo ao log:

1. **O dado é registrado em sistema de log** que pode ter retenção longa, acesso amplo, e sem controle de LGPD.
2. **O problema persiste mesmo que troquemos `console.log` por `pino`** — sem remover o campo do log explicitamente, o pino também logaria o e-mail (a menos que o redact do pino esteja configurado para `attendantEmail`, o que não está).
3. **O campo não deveria sequer ser coletado** — um sistema de feedback de qualidade de respostas não precisa do e-mail do atendente para funcionar. O identificador de sessão/token já é suficiente para associar o feedback ao atendente sem expor PII.

AGENTS.md: "Nunca logar dados pessoais (e-mail, nome)."

---

### Problema R-4: `require('@azure/cosmos')` dinâmico dentro do handler

**Trecho:** `const { CosmosClient } = require('@azure/cosmos');` dentro da função

**Categoria:** Violação de AGENTS.md

**Descrição detalhada:**

AGENTS.md: "Imports estáticos no topo (nunca require dinâmico)."

Um `require()` dentro do corpo de uma função é executado em runtime a cada chamada do handler. Problemas:

1. **Sem tree-shaking** — bundlers (esbuild, webpack) não conseguem analisar `require()` dinâmicos para eliminar código morto. O bundle fica maior.
2. **Sem análise estática** — IDEs, linters e o compilador TypeScript não validam que `@azure/cosmos` está instalado nem o tipo de `CosmosClient` em tempo de compilação.
3. **Sem detecção precoce de dependência faltando** — se `@azure/cosmos` não estiver no `node_modules`, a função sobe sem erro e só falha na primeira chamada real, em produção.
4. **Inconsistência de estilo** — o import de `@azure/functions` no topo é estático; o de `@azure/cosmos` é dinâmico. Inconsistência injustificada que confunde quem lê o código.

---

### Problema R-5: Sem tratamento de erro do Cosmos DB

**Trecho:** `await container.items.create(feedback);` sem try/catch

**Categoria:** Bug potencial

**Descrição detalhada:**

Uma chamada de rede pode falhar por throttling (429), timeout, falha transitória ou configuração incorreta. Sem tratamento:

1. A exceção não capturada do Cosmos DB vai se propagar como `UnhandledPromiseRejection`.
2. O Azure Functions v4 pode converter isso em HTTP 500, mas **sem log estruturado** — o `requestId` não aparece, o motivo do erro não é registrado de forma pesquisável.
3. O atendente recebe um erro 500 genérico sem nenhuma mensagem orientativa.

O padrão do projeto é capturar erros de dependências externas, logá-los com `logger.error` e `requestId`, e retornar `AppError` com código semântico.

---

### Problema R-6: Sem `requestId`

**Trecho:** Handler completo — nenhuma linha gera ou usa `requestId`

**Categoria:** Violação de AGENTS.md

**Descrição detalhada:**

AGENTS.md: "`requestId` (UUID v4) em todo request para rastreabilidade."

Sem `requestId`:
- Impossível correlacionar logs de uma requisição específica em produção.
- Se dois feedbacks forem enviados simultaneamente, os logs se misturam sem forma de separar.
- Em caso de bug reportado por um atendente, não há como rastrear exatamente o que aconteceu na requisição dele.

---

## Ranking por Severidade

| # | Problema | Severidade | Categoria |
|---|---|---|---|
| R-3 | `attendantEmail` logado (PII) | 🔴 Crítico | Segurança |
| R-1 | `as any` sem Zod (input não validado) | 🔴 Crítico | AGENTS.md + Segurança |
| R-5 | Sem tratamento de erro do Cosmos DB | 🟠 Alto | Bug potencial |
| R-2 | `console.log` em vez de pino | 🟡 Médio | AGENTS.md |
| R-4 | `require()` dinâmico | 🟡 Médio | AGENTS.md |
| R-6 | Sem `requestId` | 🟡 Médio | AGENTS.md |
