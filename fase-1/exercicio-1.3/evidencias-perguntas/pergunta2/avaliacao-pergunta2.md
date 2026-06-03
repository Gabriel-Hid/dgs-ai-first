# Avaliação — Pergunta 2

**Pergunta:** "Qual o SLA do cliente Gold?"  
**Data da avaliação:** 02/06/2026  
**Tier do cliente:** DESCONHECIDO (pergunta é sobre Gold)  

---

## 1. Chunks Recuperados pelo Pipeline

| # | Chunk | Score | Fonte | Relevância (conforme Anexo B) |
|---|-------|-------|-------|-------------------------------|
| 1 | SLA-2024-E | 0.560 | SLA-2024, seção 4 | ⚠️ Complementar (penalidades) |
| 2 | FAQ-41 | 0.550 | FAQ-Atendimento, item 41 | ⚠️ Pode aparecer (relevância menor) |
| 3 | SLA-2024-B | 0.543 | SLA-2024, seção 2 | ✅ DEVE ser recuperado |
| 4 | SLA-2024-C | 0.539 | SLA-2024, seção 2 | ✅ Pode aparecer (esperado pelo Anexo B) |
| 5 | SLA-2024-A | 0.537 | SLA-2024, seção 1 | ✅ Pode aparecer (esperado pelo Anexo B) |

**Retrieval:** ✅ Todos os chunks esperados pelo Anexo B foram recuperados (SLA-2024-B obrigatório + SLA-2024-A e SLA-2024-C como complementares). O pipeline também trouxe SLA-2024-E (penalidades) e FAQ-41, que agregam valor sem conflito.

---

## 2. Resposta Gerada

```
[RESPOSTA DIRETA]
O cliente Gold possui os seguintes SLAs (Fonte: SLA-2024, seção 2):

Chamados gerais:
- 1ª resposta: até 2 horas úteis
- Resolução: até 24 horas úteis

Incidentes críticos:
- 1ª resposta: até 30 minutos
- Resolução: até 4 horas

[DETALHAMENTO]
⚠️ ATENÇÃO: Para incidentes críticos de clientes Gold, o relógio de SLA NÃO pausa
fora do horário comercial (Fonte: SLA-2024, seção 2). Já para chamados gerais,
o relógio pausa fora do horário comercial (08h–18h, dias úteis).

Penalidades por descumprimento (Fonte: SLA-2024, seção 4):
- 1ª violação no mês: registro interno, sem impacto contratual
- 2ª violação no mesmo mês: crédito de 5% sobre o frete do chamado
- 3ª violação ou mais: crédito de 10% + reunião obrigatória com o gerente de conta

[FONTE(S)]
📋 SLA-2024, seções 2 e 4
```

---

## 3. Avaliação da Resposta

### 3.1. Está correta?

| Afirmação | Verificação contra documentação | Resultado |
|-----------|---------------------------------|-----------|
| Gold — resposta chamados gerais: até 2h úteis | SLA-2024, seção 2 | ✅ Correto |
| Gold — resolução chamados gerais: até 24h úteis | SLA-2024, seção 2 | ✅ Correto |
| Gold — resposta incidentes críticos: até 30min | SLA-2024, seção 2 | ✅ Correto |
| Gold — resolução incidentes críticos: até 4h | SLA-2024, seção 2 | ✅ Correto |
| Relógio NÃO pausa para incidentes críticos Gold | SLA-2024, seção 5 (presente no chunk SLA-2024-C) | ✅ Correto |
| Relógio pausa fora do horário comercial (08h-18h) para chamados gerais | SLA-2024, seção 5 (presente no chunk SLA-2024-B) | ✅ Correto |
| 1ª violação: registro interno | SLA-2024, seção 4 | ✅ Correto |
| 2ª violação: crédito 5% | SLA-2024, seção 4 | ✅ Correto |
| 3ª violação: crédito 10% + reunião com gerente de conta | SLA-2024, seção 4 | ✅ Correto |

**Resultado: ✅ CORRETA** — todas as informações factuais conferem com a documentação oficial.

### 3.2. Citou fonte?

| Informação | Citação | Formato correto? |
|------------|---------|------------------|
| SLAs de resposta e resolução | "(Fonte: SLA-2024, seção 2)" | ✅ Sim |
| Regra do relógio de SLA | "(Fonte: SLA-2024, seção 2)" | ✅ Sim |
| Penalidades por descumprimento | "(Fonte: SLA-2024, seção 4)" | ✅ Sim |

**Resultado: ✅ COMPLETA** — todas as informações factuais citadas com fonte e seção.

### 3.3. Respeitou guardrails?

| Guardrail | Cumprido? | Observação |
|-----------|-----------|------------|
| REGRA 1 — Citação obrigatória | ✅ Sim | Todas as informações com fonte |
| REGRA 2 — Proibição de invenção | ✅ Sim | Nenhum dado inventado |
| REGRA 7 — FAQ com alerta | ✅ N/A | Não utilizou FAQ-41 como fonte; usou apenas docs formais (SLA-2024) |
| Formato de resposta | ✅ Sim | Estrutura [RESPOSTA DIRETA] + [DETALHAMENTO] + [FONTE(S)] |
| Marcadores visuais | ✅ Sim | Usou ⚠️ ATENÇÃO e 📋 FONTE |
| Hierarquia de fontes | ✅ Sim | Priorizou SLA-2024 (maxima) sobre FAQ-41 (baixa) |
| Tamanho adequado | ✅ Sim | Resposta completa mas dentro do limite para procedimento multi-step |

**Resultado: ✅ GUARDRAILS RESPEITADOS**

---

## 4. Nota Geral

| Critério | Nota (1-5) | Justificativa |
|----------|------------|---------------|
| Corretude factual | 5/5 | Todos os dados corretos e verificáveis |
| Citação de fontes | 5/5 | Formato correto em todas as afirmações |
| Guardrails | 5/5 | Todos respeitados; FAQ ignorado corretamente em favor do doc formal |
| Formato | 5/5 | Seguiu estrutura exigida pelo system prompt |
| Utilidade para o atendente | 5/5 | Resposta completa: SLAs + alerta sobre relógio + penalidades |

**Nota Final: 5.0 / 5.0**

---

## 5. Análise do Retrieval

| Aspecto | Avaliação |
|---------|-----------|
| Chunks obrigatórios presentes? | ✅ SLA-2024-B recuperado |
| Chunks complementares esperados? | ✅ SLA-2024-A e SLA-2024-C presentes |
| Chunks irrelevantes? | ⚠️ FAQ-41 é redundante (info contida em SLA-2024-B com maior autoridade) |
| Ordenação por score | ⚠️ SLA-2024-E (penalidades, score 0.560) está acima de SLA-2024-B (principal, score 0.543) |

---

## 6. Propostas de Correção

### Proposta 1 — Enriquecer chunk SLA-2024-B com palavras-chave de "Gold" para priorizar retrieval

**Problema:** O chunk SLA-2024-B (dados de SLA por tier) ficou na posição 3 com score 0.543, abaixo do SLA-2024-E (penalidades, 0.560) e do FAQ-41 (0.550). Para uma query "Qual o SLA do cliente Gold?", o chunk mais relevante deveria ter o score mais alto.

**Correção no `ingest.py`:** Adicionar palavras-chave de enriquecimento com menção explícita aos tiers:

```python
# Adicionar ao chunk SLA-2024-B:
"Palavras-chave: SLA Gold, SLA Silver, SLA Standard, tempo resposta, prazo resolução, chamado geral"
```

**Resultado esperado:** SLA-2024-B sobe para posição 1 do ranking, priorizando o conteúdo mais diretamente relevante para a query.

---

### Proposta 2 — Implementar re-ranking por autoridade de documento

**Problema:** O FAQ-41 (autoridade baixa) ocupa posição 2 no ranking (score 0.550), acima de chunks de autoridade máxima (SLA-2024-B, SLA-2024-C, SLA-2024-A). Para perguntas sobre SLAs (informação contratual), chunks de fonte formal deveriam ser priorizados.

**Correção no `search.py`:** Implementar um boost de score baseado no nível de autoridade do documento:

```python
# Aplicar multiplicador de autoridade ao score final:
AUTHORITY_BOOST = {
    "maxima": 1.10,   # SLA-2024, POL-001
    "alta": 1.05,     # PROC-042-v2, PROC-042-v1
    "baixa": 0.95     # FAQ-Atendimento
}

# score_final = score_similaridade * AUTHORITY_BOOST[autoridade]
```

**Resultado esperado:** FAQ-41 cai no ranking (0.550 × 0.95 = 0.5225), ficando abaixo de todos os chunks SLA-2024. Documentos formais são priorizados automaticamente para temas contratuais.
