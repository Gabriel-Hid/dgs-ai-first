# Entregável 1 — Schema Zod do Structured Output

> Exercício 3.1 · Harness Engineering · Desenvolvedor
> Arquivo de destino no projeto: `src/shared/types.ts` (adicionado ao schema existente)

---

## Contexto

O `QueryOutputSchema` existente (definido no cenário-2, T1) já declara `source_document` como campo obrigatório com `.min(1)`. No cenário-3, formalizamos o contrato completo da resposta do assistente como `AssistantResponseSchema` — o schema que o `response-validator.ts` usa para validar cada resposta do LLM antes de entregá-la ao atendente.

**Diferença em relação ao `QueryOutputSchema`:**

| Campo | QueryOutputSchema (cenário-2) | AssistantResponseSchema (cenário-3) |
|---|---|---|
| `answer` | ✅ presente | ✅ presente |
| `source_document` | ✅ presente, `.min(1)` | ✅ presente, `.min(1)`, mensagem de erro explícita |
| `confidence_score` | ✅ presente | ✅ presente, `.min(0).max(1)` explícito |
| `.strict()` | ❌ ausente | ✅ adicionado — rejeita campos extras do LLM |

O `.strict()` é a adição crítica: sem ele, o LLM poderia retornar campos extras (ex: `hallucinated_data`, `debug_info`) que passariam silenciosamente pelo schema.

---

## Prompt Usado com o GitHub Copilot

```
Com base no QueryOutputSchema existente em src/shared/types.ts,
adicione um novo schema Zod chamado AssistantResponseSchema com os campos:
- answer: string não vazio (mensagem de erro: 'Resposta do assistente não pode ser vazia')
- source_document: string não vazio (mensagem: 'Campo source_document é obrigatório')
- confidence_score: number entre 0.0 e 1.0 inclusive

Use .strict() para rejeitar campos extras que o LLM possa retornar além do contrato.
Exporte também o tipo TypeScript derivado AssistantResponse usando z.infer.
```

---

## Schema Gerado (com ajustes aplicados)

```typescript
// Adicionado a src/shared/types.ts
// Schema do structured output — contrato da resposta do assistente de IA
// Usado pelo response-validator.ts para garantir que a resposta do LLM
// está conforme antes de ser entregue ao atendente.

export const AssistantResponseSchema = z.object({
  answer: z
    .string()
    .min(1, 'Resposta do assistente não pode ser vazia'),

  source_document: z
    .string()
    .min(1, 'Campo source_document é obrigatório — resposta sem fonte é rejeitada'),

  confidence_score: z
    .number()
    .min(0, 'confidence_score não pode ser negativo')
    .max(1, 'confidence_score não pode exceder 1.0'),
}).strict(); // Rejeita campos extras — o LLM não pode incluir campos fora do contrato

export type AssistantResponse = z.infer<typeof AssistantResponseSchema>;
```

---

## Ajustes Aplicados Após Revisão

### Ajuste 1 — `.strict()` adicionado

**O que o Copilot gerou inicialmente:**
```typescript
export const AssistantResponseSchema = z.object({
  answer: z.string().min(1),
  source_document: z.string().min(1),
  confidence_score: z.number().min(0).max(1),
});
// Sem .strict()
```

**Problema:** Um LLM pode retornar campos adicionais como `"hallucinated_source": "DOC-999"` ou `"debug_info": "..."`. Sem `.strict()`, esses campos extras passam silenciosamente pelo parse e chegam ao código downstream sem detecção. Com `.strict()`, o `safeParse` retorna erro se houver qualquer campo fora do schema — forçando a investigação.

**Correção aplicada:**
```typescript
}).strict(); // Adicionado após o fechamento do z.object({...})
```

### Ajuste 2 — Mensagens de erro explícitas nos campos

**O que o Copilot gerou inicialmente:**
```typescript
source_document: z.string().min(1),
```

**Problema:** Mensagem de erro genérica `"String must contain at least 1 character(s)"` dificulta identificar qual guardrail foi violado nos logs.

**Correção aplicada:**
```typescript
source_document: z.string().min(1, 'Campo source_document é obrigatório — resposta sem fonte é rejeitada'),
```

Com mensagens explícitas, o log do `response-validator` identifica imediatamente qual campo falhou, sem inspecionar o objeto de erro do Zod.

---

## Por que `.strict()` é necessário aqui

```
Sem .strict()                          Com .strict()
──────────────────────────────         ────────────────────────────────
LLM retorna:                           LLM retorna:
{                                      {
  answer: "...",                         answer: "...",
  source_document: "POL-001",            source_document: "POL-001",
  confidence_score: 0.9,                 confidence_score: 0.9,
  hallucinated_field: "DOC-999"  →  ❌   hallucinated_field: "DOC-999"
}                                      }
                                       safeParse retorna: { success: false }
                                       → resposta bloqueada
parse retorna: { success: true }
→ campo extra chega no código
```

No contexto de um assistente de IA, campos extras podem indicar que o modelo foi manipulado (prompt injection) ou está em modo de alucinação estruturada.

---

## Tipo Completo para Referência

```typescript
// AssistantResponse — tipo inferido do schema
type AssistantResponse = {
  answer: string;        // Resposta textual ao atendente
  source_document: string; // Documento fonte (ex: "POL-001", "SLA-2024")
  confidence_score: number; // Confiança do modelo: 0.0 (sem confiança) a 1.0 (alta)
}
```

---

## Resposta Padrão Segura (Safe Default)

Além do schema, definimos a constante de resposta segura usada pelo `response-validator.ts` em caso de falha:

```typescript
// Resposta padrão retornada quando qualquer guardrail falha
// Note: source_document usa 'SYSTEM' para indicar origem interna (não documento de negócio)
export const SAFE_DEFAULT_RESPONSE: AssistantResponse = {
  answer: 'Não foi possível processar sua solicitação. Por favor, entre em contato com o supervisor.',
  source_document: 'SYSTEM',
  confidence_score: 0,
};
```

**Por que `source_document: 'SYSTEM'`?** Em vez de string vazia (que violaria o schema), usamos um identificador que indica claramente que a resposta veio do sistema de fallback, não do pipeline RAG. Isso permite identificar nos logs quantas respostas foram substituídas pelo fallback.
