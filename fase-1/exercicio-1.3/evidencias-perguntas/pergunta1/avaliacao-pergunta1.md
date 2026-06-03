# Avaliação — Pergunta 1

**Pergunta:** "Qual o prazo de devolução?"  
**Data da avaliação:** 02/06/2026  
**Tier do cliente:** DESCONHECIDO  

---

## 1. Chunks Recuperados pelo Pipeline

| # | Chunk | Score | Fonte | Relevância (conforme Anexo B) |
|---|-------|-------|-------|-------------------------------|
| 1 | POL-001-A | 0.571 | POL-001, seção 3.1 | ✅ DEVE ser recuperado |
| 2 | FAQ-03 | 0.534 | FAQ-Atendimento, item 3 | ⚠️ Pode aparecer (relevância menor) |
| 3 | POL-001-C | 0.518 | POL-001, seção 3.3 | ⚠️ Pode aparecer |
| 4 | POL-001-D | 0.516 | POL-001, seção 3.5 | ⚠️ Pode aparecer |
| 5 | FAQ-41 | 0.507 | FAQ-Atendimento, item 41 | ❌ Irrelevante para a pergunta |

**Chunk ausente crítico:** POL-001-B (seção 3.2 — exceções ao prazo, cargas perigosas) **DEVERIA** ter sido recuperado conforme gabarito do Anexo B, mas não apareceu no Top-5.

---

## 2. Resposta Gerada

```
[RESPOSTA DIRETA]
O prazo para devolução de mercadorias é de 7 (sete) dias úteis após a data de recebimento
confirmada no sistema de tracking (Fonte: POL-001, seção 3.1).

[DETALHAMENTO]
A contagem de dias úteis exclui sábados, domingos e feriados nacionais.

⚠️ ATENÇÃO: Cargas perigosas das classes 1 a 6 da ANTT não são elegíveis para devolução
pelo processo padrão (Fonte: POL-001, seção 3.2). Antes de confirmar o prazo ao cliente,
verifique se a carga se enquadra nessa exceção.

Solicitações fora do prazo de 7 dias úteis não são elegíveis para devolução padrão —
encaminhar ao Comercial para negociação caso a caso (Fonte: POL-001, seção 3.5).

[FONTE(S)]
📋 POL-001, seções 3.1 e 3.5

[AÇÃO RECOMENDADA]
Confirme se a carga é perigosa. Se for, oriente o cliente a entrar em contato com o setor
de Gestão de Riscos (ramal 4500).
```

---

## 3. Avaliação da Resposta

### 3.1. Está correta?

| Afirmação | Verificação contra documentação | Resultado |
|-----------|---------------------------------|-----------|
| Prazo: 7 dias úteis após recebimento confirmado no tracking | POL-001, seção 3.1 | ✅ Correto |
| Exclui sábados, domingos e feriados nacionais | POL-001, seção 3.1 | ✅ Correto |
| Cargas perigosas classes 1-6 ANTT não elegíveis | POL-001, seção 3.2 | ✅ Correto |
| Prazo expirado: encaminhar ao Comercial | POL-001, seção 3.5 | ✅ Correto |
| Gestão de Riscos — ramal 4500 | POL-001, seção 3.2 + FAQ-03 | ✅ Correto |

**Resultado: ✅ CORRETA** — todas as informações factuais conferem com a documentação oficial.

### 3.2. Citou fonte?

| Informação | Citação | Formato correto? |
|------------|---------|------------------|
| Prazo 7 dias úteis | "(Fonte: POL-001, seção 3.1)" | ✅ Sim |
| Exceção cargas perigosas | "(Fonte: POL-001, seção 3.2)" | ✅ Sim |
| Prazo expirado → Comercial | "(Fonte: POL-001, seção 3.5)" | ✅ Sim |

**Resultado: ✅ COMPLETA** — todas as informações factuais foram citadas com fonte e seção no formato exigido pela REGRA 1.

### 3.3. Respeitou guardrails?

| Guardrail | Cumprido? | Observação |
|-----------|-----------|------------|
| REGRA 1 — Citação obrigatória | ✅ Sim | Todas as informações com (Fonte: ...) |
| REGRA 2 — Proibição de invenção | ✅ Sim | Nenhum dado inventado |
| REGRA 5 — Cargas perigosas | ✅ Sim | Alertou sobre exceção com ⚠️ ATENÇÃO |
| REGRA 7 — FAQ com alerta | ✅ N/A | Não usou FAQ como fonte principal; info de cargas perigosas veio da REGRA 5 do system prompt, não do FAQ-03 |
| Formato de resposta | ✅ Sim | Estrutura [RESPOSTA DIRETA] + [DETALHAMENTO] + [FONTE(S)] + [AÇÃO RECOMENDADA] |
| Marcadores visuais | ✅ Sim | Usou ⚠️ ATENÇÃO e 📋 FONTE |
| Tamanho adequado | ✅ Sim | Resposta concisa e objetiva |

**Resultado: ✅ GUARDRAILS RESPEITADOS**

---

## 4. Nota Geral

| Critério | Nota (1-5) | Justificativa |
|----------|------------|---------------|
| Corretude factual | 5/5 | Todos os dados corretos e verificáveis |
| Citação de fontes | 5/5 | Formato correto em todas as afirmações |
| Guardrails | 5/5 | Todos os guardrails aplicáveis foram respeitados |
| Formato | 5/5 | Seguiu estrutura exigida pelo system prompt |
| Utilidade para o atendente | 4/5 | Boa resposta, mas poderia ter incluído resumo do procedimento (seção 3.3) |

**Nota Final: 4.8 / 5.0**

---

## 5. Problema Identificado no Retrieval

| Problema | Impacto | Severidade |
|----------|---------|------------|
| POL-001-B (exceções) não recuperado | A exceção de cargas perigosas só apareceu na resposta porque o guardrail REGRA 5 a menciona diretamente. Sem esse guardrail, a resposta omitiria a exceção mais importante. | **Média-Alta** |
| FAQ-41 recuperado (irrelevante) | Ocupou 1 dos 5 slots de Top-K com conteúdo sobre SLA, que não tem relação com a pergunta de devolução | Baixa |

---

## 6. Propostas de Correção

### Proposta 1 — Enriquecer chunk POL-001-B para melhorar recuperação em queries de "prazo de devolução"

**Problema:** O chunk POL-001-B (seção 3.2 — exceções ao prazo) não foi recuperado porque seu conteúdo semântico foca em "cargas perigosas" e "não elegíveis", enquanto a query foca em "prazo de devolução". O embedding não associou a exceção ao tema de prazo.

**Correção no `ingest.py`:** Adicionar palavras-chave de enriquecimento semântico ao chunk POL-001-B:

```python
# No trecho de chunking da POL-001, adicionar ao POL-001-B:
"Palavras-chave: prazo devolução exceção, não elegível devolução, restrição prazo, carga perigosa prazo devolução"
```

**Resultado esperado:** POL-001-B passa a ter maior similaridade com queries sobre "prazo de devolução", aparecendo no Top-5 junto com POL-001-A. Isso elimina a dependência do guardrail hardcoded para informar a exceção.

---

### Proposta 2 — Reduzir score mínimo ou aumentar Top-K para garantir cobertura de exceções

**Problema:** Com Top-K = 5, o pipeline recuperou 3 chunks da POL-001 (A, C, D) mas perdeu o B (exceções). O FAQ-41 (irrelevante) ocupou um slot que poderia ser de POL-001-B.

**Correção no `config.py`:** Aumentar Top-K de 5 para 6 ou implementar filtro de relevância mínima:

```python
# Opção A: aumentar Top-K
TOP_K = 6

# Opção B: manter Top-K=5 mas filtrar chunks com score < 0.51 quando há chunks do mesmo documento com score > 0.55
# Isso priorizaria POL-001-B (provável score ~0.50) sobre FAQ-41 (score 0.507) se POL-001-A já estiver no resultado
```

**Resultado esperado:** Maior probabilidade de capturar chunks de exceção do mesmo documento principal, reduzindo a presença de chunks irrelevantes (FAQ-41) no contexto.
