# Avaliação — Pergunta 3

**Pergunta:** "Qual o SLA do cliente Platinum?"  
**Data da avaliação:** 02/06/2026  
**Tier do cliente:** DESCONHECIDO  

---

## 1. Chunks Recuperados pelo Pipeline

| # | Chunk | Score | Fonte | Relevância (conforme Anexo B) |
|---|-------|-------|-------|-------------------------------|
| 1 | FAQ-15 | 0.597 | FAQ-Atendimento, item 15 | ✅ Pode aparecer (relevância menor) |
| 2 | SLA-2024-A | 0.522 | SLA-2024, seção 1 | ✅ DEVE ser recuperado ("não existem outros tiers") |
| 3 | FAQ-03 | 0.496 | FAQ-Atendimento, item 3 | ❌ Irrelevante |
| 4 | SLA-2024-E | 0.494 | SLA-2024, seção 4 | ❌ Irrelevante |
| 5 | FAQ-41 | 0.491 | FAQ-Atendimento, item 41 | ❌ Irrelevante |

**Retrieval:** ✅ O chunk obrigatório (SLA-2024-A) foi recuperado conforme gabarito do Anexo B. O FAQ-15 também é esperado como relevância menor e foi corretamente posicionado. Porém, 3 dos 5 slots foram ocupados por chunks irrelevantes (FAQ-03, SLA-2024-E, FAQ-41).

---

## 2. Resposta Gerada

```
[RESPOSTA DIRETA]
❌ Não existe tier "Platinum" na NovaTech. A empresa possui exatamente três tiers de
cliente: Gold, Silver e Standard (Fonte: SLA-2024, seção 1).

[DETALHAMENTO]
A classificação de clientes da NovaTech é baseada no volume mensal de operações e no
valor do contrato:
- Gold: Contrato anual > R$ 500.000 OU > 200 operações/mês
- Silver: Contrato anual entre R$ 100.000 e R$ 500.000 OU 50–200 operações/mês
- Standard: Todos os demais clientes

Não existem outros tiers além desses três. É possível que o cliente esteja confundindo
com outra transportadora ou com o programa de fidelidade antigo descontinuado em 2022.

[FONTE(S)]
📋 SLA-2024, seção 1

[AÇÃO RECOMENDADA]
Solicite ao cliente o número do contrato para verificar o tier correto no sistema. Se o
cliente insistir em SLA diferenciado fora dos tiers existentes, encaminhe ao Comercial
para análise de viabilidade.
```

---

## 3. Avaliação da Resposta

### 3.1. Está correta?

| Afirmação | Verificação contra documentação | Resultado |
|-----------|---------------------------------|-----------|
| Tier Platinum não existe | SLA-2024, seção 1: "Não existem outros tiers além dos três listados" | ✅ Correto |
| Tiers existentes: Gold, Silver, Standard | SLA-2024, seção 1 | ✅ Correto |
| Critérios Gold: > R$ 500.000 ou > 200 op/mês | SLA-2024, seção 1 | ✅ Correto |
| Critérios Silver: R$ 100.000–500.000 ou 50–200 op/mês | SLA-2024, seção 1 | ✅ Correto |
| Critérios Standard: todos os demais | SLA-2024, seção 1 | ✅ Correto |
| Possível confusão com programa de fidelidade descontinuado em 2022 | FAQ-15 | ✅ Correto (fonte FAQ) |
| Encaminhar ao Comercial para SLA diferenciado | SLA-2024, seção 1 | ✅ Correto |

**Resultado: ✅ CORRETA** — todas as informações conferem com a documentação.

### 3.2. Citou fonte?

| Informação | Citação | Formato correto? |
|------------|---------|------------------|
| Tier Platinum não existe | "(Fonte: SLA-2024, seção 1)" | ✅ Sim |
| Classificação dos tiers | Implícita pela mesma fonte | ✅ Sim |
| Programa de fidelidade descontinuado em 2022 | Não citou FAQ-15 explicitamente | ⚠️ Parcial |

**Resultado: ⚠️ PARCIAL** — a informação sobre "programa de fidelidade antigo descontinuado em 2022" veio exclusivamente do FAQ-15 mas não foi citada com fonte nem acompanhada do alerta da REGRA 7.

### 3.3. Respeitou guardrails?

| Guardrail | Cumprido? | Observação |
|-----------|-----------|------------|
| REGRA 1 — Citação obrigatória | ⚠️ Parcial | Faltou citar FAQ-15 como fonte da info sobre programa descontinuado |
| REGRA 2 — Proibição de invenção | ✅ Sim | Nenhum dado inventado; não inventou SLA para Platinum |
| REGRA 4 — Tiers de cliente | ✅ Sim | Informou que não existe, citou fonte, solicitou nº do contrato |
| REGRA 7 — FAQ com alerta | ❌ Não | Usou informação do FAQ-15 ("programa de fidelidade descontinuado em 2022") sem incluir o alerta obrigatório |
| Formato de resposta | ✅ Sim | Estrutura completa com marcadores visuais |
| Marcadores visuais | ✅ Sim | Usou ❌ e 📋 |

**Resultado: ⚠️ PARCIAL** — falha na REGRA 7 ao usar informação do FAQ sem alerta.

---

## 4. Nota Geral

| Critério | Nota (1-5) | Justificativa |
|----------|------------|---------------|
| Corretude factual | 5/5 | Todas as informações corretas |
| Citação de fontes | 4/5 | Faltou citação explícita do FAQ-15 |
| Guardrails | 4/5 | REGRA 7 não aplicada para info do FAQ-15 |
| Formato | 5/5 | Estrutura e marcadores corretos |
| Utilidade para o atendente | 5/5 | Resposta clara, ação recomendada precisa |

**Nota Final: 4.6 / 5.0**

---

## 5. Análise do Retrieval

| Aspecto | Avaliação |
|---------|-----------|
| Chunks obrigatórios presentes? | ✅ SLA-2024-A recuperado |
| Chunks complementares esperados? | ✅ FAQ-15 presente |
| Chunks irrelevantes? | ⚠️ FAQ-03 (carga perigosa), SLA-2024-E (penalidades) e FAQ-41 (SLA resposta/resolução) são irrelevantes para a pergunta |
| Eficiência do Top-K | ⚠️ Apenas 2 de 5 chunks são realmente relevantes; 3 slots desperdiçados |

---

## 6. Propostas de Correção

### Proposta 1 — Incluir alerta da REGRA 7 sempre que informação do FAQ for incorporada à resposta

**Problema:** A resposta usou a informação do FAQ-15 ("programa de fidelidade antigo descontinuado em 2022") como contexto complementar sem incluir o alerta obrigatório da REGRA 7, nem citar o FAQ-15 como fonte. Embora a informação principal (tier não existe) venha do documento formal SLA-2024, a explicação adicional sobre o motivo da confusão do cliente veio exclusivamente do FAQ.

**Correção no system prompt (REGRA 7):** Tornar mais explícito que o alerta se aplica a qualquer informação retirada de chunks FAQ, mesmo quando usada como complemento a uma fonte formal:

```
REGRA 7 (refinada): Se QUALQUER afirmação da resposta tiver como única fonte um chunk
FAQ-XX — mesmo que outras partes da resposta usem documentos formais — essa afirmação
específica deve ser acompanhada do alerta:
"⚠️ Esta informação é baseada no FAQ interno..."
OU ser removida da resposta caso não agregue valor essencial.
```

**Resultado esperado:** O LLM passa a identificar individualmente quais partes da resposta vêm do FAQ e aplica o alerta seletivamente, em vez de omitir a atribuição.

---

### Proposta 2 — Reduzir ruído no retrieval com filtro de score mínimo relativo

**Problema:** 3 de 5 chunks recuperados (FAQ-03, SLA-2024-E, FAQ-41) são irrelevantes para a pergunta "Qual o SLA do cliente Platinum?". O gap de score entre o chunk mais relevante (FAQ-15: 0.597) e os irrelevantes (0.491–0.496) é significativo (~0.10), indicando que esses chunks têm baixa confiança de relevância.

**Correção no `search.py`:** Implementar um filtro de score mínimo relativo ao melhor resultado:

```python
# Descartar chunks com score < 75% do melhor score
melhor_score = resultados[0]["score"]
threshold = melhor_score * 0.75  # ex: 0.597 * 0.75 = 0.448

# Neste caso, todos passariam (0.491 > 0.448), então usar threshold mais agressivo:
threshold = melhor_score * 0.85  # ex: 0.597 * 0.85 = 0.507

# Resultado: FAQ-03 (0.496), SLA-2024-E (0.494) e FAQ-41 (0.491) seriam descartados
# Apenas FAQ-15 e SLA-2024-A seriam enviados ao LLM
```

**Resultado esperado:** Contexto mais limpo com apenas chunks relevantes, reduzindo risco de o LLM usar informações de chunks irrelevantes e diminuindo o custo de tokens.
