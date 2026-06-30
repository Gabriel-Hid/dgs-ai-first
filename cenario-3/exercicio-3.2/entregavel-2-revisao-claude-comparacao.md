# Entregável 2 — Revisão do Claude e Comparação

> Exercício 3.2 · Revisão Crítica de Outputs de IA · Desenvolvedor
> Esta revisão foi feita APÓS a revisão humana (entregável-1), seguindo a disciplina do exercício.

---

## Prompt Usado com o Claude

```
Faça uma revisão de código detalhada do módulo feedback-handler.ts abaixo.

Contexto do projeto (AGENTS.md):
- TypeScript strict mode
- Zod obrigatório para validação de input
- pino para logging (nunca console.log)
- Nunca logar dados pessoais (e-mail, nome, conteúdo de PII)
- Imports estáticos no topo do arquivo (nunca require dinâmico)
- requestId (UUID v4) em todo request para rastreabilidade

Para cada problema encontrado, classifique como:
1. Violação de AGENTS.md
2. Problema de segurança
3. Bug potencial

Seja específico: cite o trecho exato, explique o impacto e sugira a correção.

[código colado]
```

---

## Revisão do Claude

### C-1: `as any` — ausência de validação de input

> **Trecho:** `const body = await request.json() as any;`
>
> **Classificação:** Violação de AGENTS.md + Problema de segurança
>
> **Claude:** "O cast `as any` descarta completamente a tipagem TypeScript para o body da requisição. Sem um schema Zod, campos obrigatórios como `queryId` ou `rating` podem estar ausentes, ter tipo errado, ou conter valores fora do range esperado — e nada impede que esses dados corrompidos sejam persistidos no Cosmos DB. Um atacante pode enviar payloads malformados que causam comportamento inesperado downstream. A correção é definir um `FeedbackBodySchema` com Zod e usar `safeParse`, retornando 400 com `ValidationError` se o input for inválido."

---

### C-2: `console.log` — violação de logging

> **Trecho:** `console.log('Feedback recebido:', JSON.stringify(feedback));`
>
> **Classificação:** Violação de AGENTS.md
>
> **Claude:** "O projeto usa `pino` como logger estruturado. `console.log` não produz JSON estruturado, não tem níveis configuráveis, não integra com Azure Monitor e não tem suporte a redação de campos sensíveis. Substituir por `logger.info({ requestId, queryId: feedback.queryId, rating: feedback.rating }, 'Feedback recebido')` — sem serializar o objeto completo."

---

### C-3: `attendantEmail` sendo coletado e logado — PII

> **Trecho:** `attendantEmail: body.attendantEmail` no objeto `feedback` + serialização no `console.log`
>
> **Classificação:** Problema de segurança
>
> **Claude:** "O e-mail do atendente é um dado pessoal. Além de ser logado (violação direta do AGENTS.md), ele está sendo persistido no Cosmos DB. O design deveria ser questionado: um registro de feedback de qualidade de resposta precisa mesmo armazenar o e-mail? Se o objetivo é associar o feedback a um atendente, um identificador de sessão anônimo ou o ID do usuário (não o e-mail) seria suficiente e menos arriscado. A correção mínima é remover o campo do schema Zod e do objeto persistido."

---

### C-4: `require()` dinâmico — violação de imports estáticos

> **Trecho:** `const { CosmosClient } = require('@azure/cosmos');`
>
> **Classificação:** Violação de AGENTS.md
>
> **Claude:** "Import dentro do corpo do handler é um antipadrão explicitamente proibido pelo AGENTS.md. Além da violação estilística, um `require()` dinâmico impede que o TypeScript valide os tipos de `CosmosClient` e que o bundler faça tree-shaking. A dependência deveria ser importada no topo do arquivo com `import { CosmosClient } from '@azure/cosmos';`."

---

### C-5: Ausência de `requestId`

> **Trecho:** Handler completo — sem geração de `requestId`
>
> **Classificação:** Violação de AGENTS.md
>
> **Claude:** "Todo handler do projeto deve gerar um `requestId` (UUID v4) no início do fluxo e incluí-lo em todos os logs. Sem ele, é impossível correlacionar logs de uma mesma requisição em produção. Usar `randomUUID()` de `node:crypto` — consistente com o padrão do query endpoint."

---

### C-6: Sem tratamento de erro do Cosmos DB

> **Trecho:** `await container.items.create(feedback);` sem try/catch
>
> **Classificação:** Bug potencial
>
> **Claude:** "Uma operação de escrita no Cosmos DB pode falhar por throttling (HTTP 429), timeout, ou falha de rede. Sem try/catch, a exceção se propaga como `UnhandledPromiseRejection`. O padrão do projeto é capturar erros de dependências externas em um bloco catch, logá-los com `logger.error({ requestId, err })` e retornar HTTP 500 com mensagem segura para o cliente. Nenhum detalhe interno deve ser exposto na resposta."

---

### C-7 (exclusivo Claude): `process.env.COSMOS_CONNECTION_STRING` pode ser `undefined`

> **Trecho:** `new CosmosClient(process.env.COSMOS_CONNECTION_STRING)`
>
> **Classificação:** Bug potencial
>
> **Claude:** "Em TypeScript strict, `process.env.X` tem tipo `string | undefined`. Passar `undefined` para o construtor do `CosmosClient` pode resultar em erro de runtime não informativo. O padrão do projeto usa `requireEnv()` em `config.ts`, que lança um erro claro com o nome da variável faltante no startup da função — muito mais diagnóstico do que uma falha silenciosa na primeira chamada de produção."

---

### C-8 (exclusivo Claude): Retorno `body: 'OK'` como string em vez de objeto JSON

> **Trecho:** `return { status: 200, body: 'OK' };`
>
> **Classificação:** Bug potencial
>
> **Claude:** "O Azure Functions v4 com clientes que esperam JSON receberão `'OK'` como string crua, não como JSON. O padrão do projeto é usar `jsonBody` (não `body`) para retornar objetos, e `body` para strings. Adicionalmente, o status correto para criação de recurso é 201, não 200. A correção: `return { status: 201, jsonBody: { success: true } };`"

---

## Comparação: Revisão Humana vs Claude

| Problema | Revisão Humana | Claude | Observação |
|---|---|---|---|
| `as any` sem Zod | ✅ R-1 | ✅ C-1 | Coincidência — mesma análise de impacto (dados corrompidos no Cosmos) |
| `console.log` em vez de pino | ✅ R-2 | ✅ C-2 | Coincidência — mesma classificação AGENTS.md |
| `attendantEmail` logado (PII) | ✅ R-3 | ✅ C-3 | Coincidência — Claude foi além: questionou se o campo deveria sequer existir |
| `require()` dinâmico | ✅ R-4 | ✅ C-4 | Coincidência — mesma categorização |
| Sem tratamento de erro Cosmos | ✅ R-5 | ✅ C-6 | Coincidência — mesmos riscos identificados |
| Sem `requestId` | ✅ R-6 | ✅ C-5 | Coincidência — mesma referência ao AGENTS.md |
| `process.env` direto (undefined) | ❌ não identificado | ✅ C-7 | **Exclusivo Claude** — `requireEnv()` como falha rápida no startup |
| Status 200 / `body` vs `jsonBody` | ❌ não identificado | ✅ C-8 | **Exclusivo Claude** — status 201 + distinção `body`/`jsonBody` do AZ Functions v4 |
| **Total** | **6 problemas** | **8 problemas** | **6/6 coincidências + 2 exclusivos do Claude** |

---

## Reflexão Honesta

**Pontos onde o Claude foi além da revisão humana (exclusivos):**

1. **C-7 (`process.env` direto):** A revisão humana não identificou que `process.env.COSMOS_CONNECTION_STRING` tem tipo `string | undefined` e pode causar erro de runtime não informativo. O Claude conectou esse ponto ao padrão `requireEnv()` de `config.ts` do projeto — uma falha rápida e clara no startup é muito mais diagnóstica do que uma exceção obscura na primeira chamada em produção.

2. **C-8 (status 200 / `body` vs `jsonBody`):** A revisão humana não chegou ao detalhe do status de retorno nem à distinção entre `body` (string crua) e `jsonBody` (objeto JSON) da API do Azure Functions v4. O Claude identificou que `return { status: 200, body: 'OK' }` tem dois problemas: status semântico incorreto (deveria ser 201 Created) e uso de `body` em vez de `jsonBody` para retorno de objeto.

**Pontos onde a revisão humana e o Claude foram equivalentes:**

Os 6 problemas identificados pela revisão humana (R-1 a R-6) foram todos confirmados pelo Claude com classificação equivalente. Não houve caso em que a revisão humana identificou algo que o Claude não viu.

**Divergências de avaliação:**

Nenhuma divergência de classificação nos pontos coincidentes — os dois concordaram na categoria (AGENTS.md / segurança / bug) de cada problema.

**Observação sobre o exercício:**

A revisão humana feita antes do Claude foi essencial para a comparação ter valor. Se o Claude fosse consultado primeiro, a "revisão humana" seria contaminada. O fluxo correto (humano → IA → comparação) é a única forma de medir genuinamente onde cada abordagem adiciona valor.
