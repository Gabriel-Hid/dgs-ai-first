# Entregável 3 — Code Review do response-validator.ts

> Exercício 3.1 · Harness Engineering · Desenvolvedor
> Fase: revisão crítica do código gerado pelo GitHub Copilot

---

## Processo

O fluxo seguiu a disciplina do exercício:
1. **Revisão humana** (própria) — antes de usar qualquer ferramenta de IA.
2. **Revisão com Claude** — segundo par de olhos, prompt estruturado.
3. **Comparação honesta** — concordâncias, divergências, pontos únicos de cada lado.
4. **Correções aplicadas** — código final com cada ajuste documentado.

---

## Parte 1 — Revisão Humana (antes do Claude)

### Versão inicial gerada pelo Copilot

O Copilot gerou uma versão funcional, mas com os seguintes problemas identificados na revisão própria:

---

### Problema H-1: Schema sem `.strict()` — campos extras passam silenciosamente

**Trecho original:**
```typescript
export const AssistantResponseSchema = z.object({
  answer: z.string().min(1),
  source_document: z.string().min(1),
  confidence_score: z.number().min(0).max(1),
});
// Sem .strict()
```

**Categoria:** Bug potencial

**Por que é problema:** Um LLM instruído com JSON mode pode retornar campos extras além do contrato (`hallucinated_source`, `debug`, `override_guardrail`). Sem `.strict()`, esses campos passam pelo `safeParse` com `success: true` e chegam ao código downstream sem detecção. No contexto de prompt injection, um campo extra pode ser um vetor de ataque.

**Impacto:** O guardrail de schema fica parcialmente ineficaz — a validação "passa" mesmo com payload inválido.

---

### Problema H-2: Regex do Guardrail 2 muito simples — não cobre paráfrases

**Trecho original gerado pelo Copilot:**
```typescript
const DANGEROUS_GOODS_REGEX = /carga perigosa.*devolu[çc][aã]o|devolu[çc][aã]o.*carga perigosa/i;
```

**Categoria:** Bug potencial + Violação de AGENTS.md (guardrail não cobre o contrato)

**Por que é problema:** O regex original:
- Exige que "carga perigosa" e "devolução" apareçam contíguos na mesma direção — não cobre frases como "Sim, **cargas perigosas** (plural) **podem ser devolvidas**".
- Não cobre "devolver" (infinitivo), "devolvida" (particípio), "devolve" (presente).
- Não verifica a presença de negativas — poderia bloquear "Cargas perigosas **não** podem ser devolvidas" (resposta correta!).

**Exemplo de falso negativo (não bloquearia quando deveria):**
```
"Pode devolver a carga perigosa mediante autorização"
→ Regex original: não captura porque "devolver" ≠ "devolução"
→ Resposta incorreta passa ao atendente
```

**Exemplo de falso positivo (bloquearia quando não deveria):**
```
"Não é possível efetuar devolução de carga perigosa — POL-001"
→ Regex original: captura "devolução" + "carga perigosa" → BLOQUEIA
→ Resposta correta é erroneamente bloqueada
```

---

### Problema H-3: Log expõe `response.answer` completo

**Trecho original:**
```typescript
logger.warn(
  { requestId, reason: 'GUARDRAIL_DANGEROUS_GOODS', answer: response.answer },
  'GR-2 violado'
);
```

**Categoria:** Problema de segurança

**Por que é problema:** O campo `answer` pode conter informações sensíveis inseridas por prompt injection, dados pessoais mencionados pelo atendente na pergunta original, ou conteúdo problemático que o guardrail acabou de bloquear. Logar esse conteúdo em logs persistentes viola o princípio do AGENTS.md ("nunca logar dados pessoais") e pode criar evidência de conteúdo indesejado em sistemas de auditoria.

---

### Problema H-4: Tipo de retorno da função não declarado explicitamente

**Trecho original:**
```typescript
export function validateAssistantResponse(rawResponse: unknown, requestId: string) {
  // TypeScript infere o tipo de retorno
```

**Categoria:** Violação de AGENTS.md (TypeScript strict — sem inferência de tipo em funções públicas)

**Por que é problema:** Em TypeScript strict mode, funções públicas (exportadas) devem ter tipo de retorno explícito. Sem ele, uma mudança no corpo da função pode alterar silenciosamente o tipo inferido e quebrar callers de forma não imediata.

---

### Problema H-5: `source_document.trim()` não verificado após schema pass

**Trecho original:**
```typescript
// Guardrail 1: source_document ausente
if (!response.source_document) { // só verifica falsy
```

**Categoria:** Bug potencial

**Por que é problema:** O schema Zod garante `.min(1)`, então `response.source_document` nunca será string vazia `""`. Mas o Zod não faz trim — uma resposta do LLM com `source_document: "   "` (três espaços) passa pelo `.min(1)` (tem comprimento 3) mas é semanticamente vazia. A verificação `!response.source_document` também passa para `"   "` porque `"   "` é truthy. Resultado: resposta com fonte "vazia" chega ao atendente.

---

## Parte 2 — Revisão com Claude

### Prompt usado

```
Faça um code review do módulo response-validator.ts abaixo. Contexto:
- Projeto TypeScript strict mode (AGENTS.md)
- Regras: Zod para validação, pino para logging, sem console.log, sem require dinâmico,
  nunca logar dados pessoais, imports estáticos no topo
- Guardrail 2 deve cobrir variações de "carga perigosa" + "devolução" afirmativa,
  incluindo plural, formas verbais e MUST verificar ausência de negativas

Identifique problemas reais, classificando como:
- Violação de AGENTS.md
- Problema de segurança
- Bug potencial

[código colado]
```

### Problemas identificados pelo Claude

**C-1: Schema sem `.strict()`** *(coincide com H-1)*
> "O schema Zod aceita campos extras. Um LLM com output mode ligeiramente diferente poderia retornar propriedades adicionais que passariam pela validação sem detecção. Adicionar `.strict()` rejeita qualquer propriedade fora do contrato."
> Classificação: Bug potencial

**C-2: Regex não cobre plural e formas verbais** *(coincide com H-2)*
> "O pattern `/carga perigosa.*devolu/i` não cobre 'cargas perigosas', 'devolver', 'devolvida' nem verifica a ausência de negativas. Uma resposta como 'Sim, pode devolver a carga perigosa' passaria sem ser bloqueada."
> Classificação: Bug potencial + falha no guardrail de negócio

**C-3: Log do conteúdo da resposta** *(coincide com H-3)*
> "O campo `answer` está sendo logado em `logger.warn`. Em um sistema de atendimento, o `answer` pode conter informações derivadas de perguntas do atendente que incluam dados de clientes. Logar o campo completo é risco de PII."
> Classificação: Problema de segurança

**C-4: Tipo de retorno não declarado** *(coincide com H-4)*
> "Função exportada sem tipo de retorno explícito. Em TypeScript strict, isso é inconsistente com o padrão do projeto."
> Classificação: Violação de AGENTS.md

**C-5 (exclusivo Claude): `satisfies` operator para type-safety dos reason strings**
> "Os strings de `reason` como `'SCHEMA_INVALID'` estão sendo passados como literais. Usar `satisfies GuardrailViolation` garante que o compilador valide que o literal é membro do union type, evitando typos que só apareceriam em runtime."
> Classificação: Bug potencial (typo silencioso)

**C-6 (exclusivo Claude): Ausência de teste de que o validator trata `null` e `undefined`**
> "A função recebe `rawResponse: unknown`. Se o LLM retorna `null` ou `undefined` (timeout, resposta vazia), o `safeParse` trata corretamente — mas o código não documenta explicitamente esse comportamento esperado, e não há teste para ele."
> Classificação: Não é bug (Zod trata), mas é gap de documentação/teste.

---

## Parte 3 — Comparação Honesta

| Problema | Revisão Humana | Claude | Coincidência |
|---|---|---|---|
| Schema sem `.strict()` | ✅ H-1 | ✅ C-1 | Sim — ambos identificaram como prioritário |
| Regex insuficiente (plural, formas verbais, negativas) | ✅ H-2 | ✅ C-2 | Sim — ambos detalharam os casos não cobertos |
| Log expondo `answer` (PII risk) | ✅ H-3 | ✅ C-3 | Sim — mesma categoria (segurança) |
| Tipo de retorno não declarado | ✅ H-4 | ✅ C-4 | Sim — mesma classificação AGENTS.md |
| `source_document.trim()` não verificado | ✅ H-5 | ❌ não mencionou | **Único da revisão humana** |
| `satisfies` operator para reason strings | ❌ não mencionou | ✅ C-5 | **Único do Claude** |
| Ausência de teste para null/undefined | ❌ não mencionou | ✅ C-6 | **Único do Claude** (gap de teste, não bug) |

### Reflexão

**O que o Claude encontrou que eu não vi:** O uso do `satisfies` operator é uma melhoria real — sem ele, um typo no reason string como `'GUARDRAIL_SOURCE_MISSIN'` (sem 'G') compilaria sem erro e só falharia em runtime quando o caller fizesse switch/match no tipo. O Claude foi mais atento à type-safety de strings literais.

**O que eu encontrei que o Claude não mencionou:** A verificação de `trim()` no `source_document` é um edge case real — Zod valida comprimento (`.min(1)`), não conteúdo semântico. Uma string de espaços tem comprimento > 0 mas é semanticamente inválida. O Claude focou no que é mais óbvio no diff de código e não chegou nesse edge case de validação.

**Divergência de avaliação:** Nenhuma — todos os problemas identificados por ambos tiveram classificação equivalente.

---

## Parte 4 — Correções Aplicadas no Código Final

### Correção 1 — `.strict()` no schema

```typescript
// ANTES
export const AssistantResponseSchema = z.object({
  answer: z.string().min(1),
  source_document: z.string().min(1),
  confidence_score: z.number().min(0).max(1),
});

// DEPOIS
export const AssistantResponseSchema = z.object({
  answer: z.string().min(1, 'Resposta do assistente não pode ser vazia'),
  source_document: z.string().min(1, 'Campo source_document é obrigatório — resposta sem fonte é rejeitada'),
  confidence_score: z.number().min(0).max(1),
}).strict(); // ← adicionado
```

**Impacto:** Campos extras do LLM agora causam falha de schema e são bloqueados antes de chegar aos guardrails de conteúdo.

---

### Correção 2 — Regex do Guardrail 2 reescrito

```typescript
// ANTES — um único regex, não cobre plural nem negativas
const DANGEROUS_GOODS_REGEX = /carga perigosa.*devolu[çc][aã]o|devolu[çc][aã]o.*carga perigosa/i;

// DEPOIS — três regex separados com lógica explícita
const DANGEROUS_GOODS_PATTERN = /cargas?\s+perigosas?/i;          // singular e plural
const RETURN_AFFIRMATIVE_PATTERN = /devolu[çc][aã]o|devolver|devolvid[ao]s?|devolv[eê]/i; // formas verbais
const NEGATION_PATTERN = /\bn[aã]o\b|impossível|impossivel|proibid[ao]|vedad[ao]|n[aã]o\s+(é\s+)?possível|n[aã]o\s+pode|n[aã]o\s+permit/i;

// Lógica:
if (hasDangerousGoods && hasReturnAffirmative && !hasNegation) {
  // BLOQUEAR — afirmação positiva de devolução de carga perigosa
}
```

**Cobertura dos casos:**

| Texto | Antes | Depois |
|---|---|---|
| "Sim, pode devolver a carga perigosa" | ❌ não bloqueava | ✅ bloqueia |
| "Cargas perigosas podem ser devolvidas" | ❌ não bloqueava (plural) | ✅ bloqueia |
| "A devolução é permitida para carga perigosa" | ✅ bloqueava | ✅ bloqueia |
| "Não é possível devolver carga perigosa" | ❌ bloqueava (falso positivo) | ✅ não bloqueia (negativa presente) |
| "Cargas perigosas não podem ser devolvidas" | ❌ bloqueava (falso positivo) | ✅ não bloqueia |

---

### Correção 3 — Log não expõe `answer`

```typescript
// ANTES — loga o conteúdo completo da resposta
logger.warn(
  { requestId, reason: 'GUARDRAIL_DANGEROUS_GOODS', answer: response.answer },
  'GR-2 violado'
);

// DEPOIS — loga apenas metadados (sem conteúdo da resposta)
logger.warn(
  {
    requestId,
    reason: 'GUARDRAIL_DANGEROUS_GOODS' satisfies GuardrailViolation,
    confidence_score: response.confidence_score,
    source_document: response.source_document,
    // answer NÃO é logado — pode conter PII ou conteúdo sensível
  },
  'GR-2 violado: resposta afirma devolução de carga perigosa — bloqueada por POL-001 seção 3.2',
);
```

---

### Correção 4 — Tipo de retorno explícito

```typescript
// ANTES — tipo inferido
export function validateAssistantResponse(rawResponse: unknown, requestId: string) {

// DEPOIS — tipo declarado explicitamente
export function validateAssistantResponse(
  rawResponse: unknown,
  requestId: string,
): ValidatorResult {
```

---

### Correção 5 — `.trim()` na verificação do source_document

```typescript
// ANTES — falha para "   " (espaços passam pelo Zod .min(1) mas são semanticamente vazios)
if (!response.source_document) {

// DEPOIS — detecta strings com apenas espaços
if (!response.source_document.trim()) {
```

---

### Correção 6 — `satisfies` operator para reason strings (sugestão do Claude)

```typescript
// ANTES — string literal sem validação de tipo
logger.warn({ requestId, reason: 'SCHEMA_INVALID' }, 'msg');

// DEPOIS — satisfies garante que o literal é membro do union type
logger.warn(
  { requestId, reason: 'SCHEMA_INVALID' satisfies GuardrailViolation },
  'msg'
);
```

**Impacto:** Typos no reason string são detectados em compile time, não em runtime.

---

## Distinção: Prompt (Probabilístico) vs Código (Determinístico)

Esta distinção é o ponto central do exercício 3.1:

| Mecanismo | Onde atua | Confiabilidade | Exemplo no projeto |
|---|---|---|---|
| **System prompt** | Antes da geração | ~88% (12% de falhas observadas em teste) | "Cite sempre a fonte do documento" |
| **Structured output (schema Zod)** | Pós-geração, pré-envio | 100% — código não "esquece" | `AssistantResponseSchema.safeParse()` |
| **Guardrail determinístico (código)** | Pós-geração, pré-envio | 100% — regex/código não tem variação | Verificação de "carga perigosa + devolução" |
| **HITL** | Casos de borda | N/A — decisão humana | `confidence_score < 0.5` em tópico sensível |

O `response-validator.ts` implementa as duas camadas de código (structured output + guardrails determinísticos). O sistema prompt continua existindo como primeira linha de defesa; o validator é a garantia que não depende do comportamento do modelo.

**Por que as duas camadas são necessárias e complementares:**
- O prompt garante que, na maioria dos casos, o LLM produz o formato correto e o conteúdo adequado. Isso reduz a carga dos guardrails de código.
- O código garante que os casos onde o prompt falha (12% observado) são interceptados deterministicamente antes de chegar ao atendente.
- O HITL garante que os casos de borda (baixa confiança em tópico sensível) não são decididos automaticamente.
