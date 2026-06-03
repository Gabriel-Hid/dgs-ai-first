# Avaliação — Pergunta 5

**Pergunta:** "O que acontece com carga danificada?"  
**Data da avaliação:** 02/06/2026  
**Tier do cliente:** DESCONHECIDO  

---

## 1. Chunks Recuperados pelo Pipeline

| # | Chunk | Score | Fonte | Relevância (conforme Anexo B) |
|---|-------|-------|-------|-------------------------------|
| 1 | FAQ-38 | 0.687 | FAQ-Atendimento, item 38 | ✅ DEVE ser recuperado |
| 2 | FAQ-22 | 0.634 | FAQ-Atendimento, item 22 | ❌ Irrelevante (seguro de carga) |
| 3 | FAQ-32 | 0.615 | FAQ-Atendimento, item 32 | ❌ Irrelevante (carga perigosa + frete expresso) |
| 4 | FAQ-03 | 0.546 | FAQ-Atendimento, item 3 | ❌ Irrelevante (devolução carga perigosa) |
| 5 | SLA-2024-D | 0.544 | SLA-2024, seção 3 | ❌ Irrelevante (definição incidente crítico) |

**Retrieval:** ✅ O chunk obrigatório (FAQ-38) foi recuperado conforme gabarito do Anexo B. Porém, conforme nota do Anexo B: "Nenhum documento formal cobre isso" — portanto esta é uma situação onde a REGRA 7 DEVE ser aplicada obrigatoriamente.

---

## 2. Resposta Gerada

```
[RESPOSTA DIRETA]
Carga danificada em trânsito segue um processo diferente do processo padrão de devolução.
O cliente deve registrar a ocorrência em até 48 horas após o recebimento, com fotos e
laudo se possível.

[DETALHAMENTO]
O procedimento para carga danificada é:
1. Cliente registra ocorrência em até 48h após recebimento (com fotos e laudo)
2. A NovaTech investiga a responsabilidade
3. Se comprovada responsabilidade da NovaTech, reembolso integral
4. O processo é conduzido pelo Jurídico, não pelo atendimento normal

⚠️ Esta informação é baseada no FAQ interno do time de atendimento, que não foi
validado por Compliance ou Operações. Confirme com o supervisor antes de passar ao cliente.

[FONTE(S)]
📋 FAQ-Atendimento, item 38

[AÇÃO RECOMENDADA]
↗️ Encaminhe o cliente para o e-mail sinistros@novatech.com.br. Este processo não é
tratado pelo atendimento normal.
```

---

## 3. Avaliação da Resposta

### 3.1. Está correta?

| Afirmação | Verificação contra documentação | Resultado |
|-----------|---------------------------------|-----------|
| Carga danificada tem processo diferente de devolução | FAQ-38 | ✅ Correto |
| Registrar ocorrência em até 48h após recebimento | FAQ-38 | ✅ Correto |
| Com fotos e laudo se possível | FAQ-38 | ✅ Correto |
| NovaTech investiga responsabilidade | FAQ-38 | ✅ Correto |
| Se responsabilidade da NovaTech, reembolso integral | FAQ-38 | ✅ Correto |
| Processo conduzido pelo Jurídico | FAQ-38 | ✅ Correto |
| Encaminhar para sinistros@novatech.com.br | FAQ-38 | ✅ Correto |

**Resultado: ✅ CORRETA** — todas as informações correspondem ao FAQ-38.

### 3.2. Citou fonte?

| Informação | Citação | Formato correto? |
|------------|---------|------------------|
| Procedimento de carga danificada | "📋 FAQ-Atendimento, item 38" | ✅ Sim |
| Alerta de FAQ como única fonte | Alerta da REGRA 7 incluído | ✅ Sim |

**Resultado: ✅ COMPLETA** — fonte citada corretamente e alerta obrigatório incluído.

### 3.3. Respeitou guardrails?

| Guardrail | Cumprido? | Observação |
|-----------|-----------|------------|
| REGRA 1 — Citação obrigatória | ✅ Sim | FAQ-38 citado como fonte |
| REGRA 2 — Proibição de invenção | ✅ Sim | Nenhum dado inventado |
| REGRA 7 — FAQ com alerta | ✅ Sim | Alerta obrigatório incluído na íntegra |
| REGRA 6 — Tópicos sem cobertura | ⚠️ Parcial | Poderia ter mencionado que não há documento formal sobre este tópico |
| Formato de resposta | ✅ Sim | Estrutura completa |
| Marcadores visuais | ✅ Sim | Usou ⚠️, 📋 e ↗️ |

**Resultado: ✅ GUARDRAILS RESPEITADOS** — a aplicação da REGRA 7 foi o ponto mais importante e foi cumprida corretamente.

---

## 4. Nota Geral

| Critério | Nota (1-5) | Justificativa |
|----------|------------|---------------|
| Corretude factual | 5/5 | Informações do FAQ-38 reproduzidas corretamente |
| Citação de fontes | 5/5 | Fonte citada e classificada como FAQ (não formal) |
| Guardrails | 5/5 | REGRA 7 aplicada perfeitamente — alerta incluído |
| Formato | 5/5 | Estrutura, marcadores e tamanho adequados |
| Utilidade para o atendente | 5/5 | Resposta clara com ação prática (e-mail de encaminhamento) |

**Nota Final: 5.0 / 5.0**

---

## 5. Análise do Retrieval

| Aspecto | Avaliação |
|---------|-----------|
| Chunks obrigatórios presentes? | ✅ FAQ-38 recuperado com score alto (0.687) |
| Cobertura formal | ❌ Conforme esperado — Anexo B confirma: "Nenhum documento formal cobre isso" |
| Chunks irrelevantes? | ⚠️ FAQ-22, FAQ-32, FAQ-03 e SLA-2024-D não agregam valor |
| Eficiência do Top-K | ⚠️ Apenas 1 de 5 chunks é realmente relevante |

**Observação positiva:** Esta é uma armadilha intencional do Anexo B — o FAQ-38 é a única fonte disponível e não tem respaldo em documento formal. O comportamento correto é responder com o FAQ + alerta da REGRA 7, que foi exatamente o que aconteceu.

---

## 6. Propostas de Correção

### Proposta 1 — Truncar contexto quando apenas 1 chunk é relevante (filtro de gap de score)

**Problema:** 4 de 5 chunks enviados ao LLM são irrelevantes (FAQ-22, FAQ-32, FAQ-03, SLA-2024-D). Embora neste caso o LLM tenha ignorado corretamente os chunks irrelevantes, enviar contexto desnecessário aumenta custo de tokens e pode confundir modelos menos capazes.

**Correção no `search.py`:** Implementar detecção de "gap de relevância" — se há um gap significativo entre o melhor chunk e os demais, enviar apenas os chunks acima do gap:

```python
def filter_by_relevance_gap(results: list, gap_threshold: float = 0.05) -> list:
    """Remove chunks que estão significativamente abaixo do melhor score."""
    if not results:
        return results
    
    best_score = results[0]["score"]
    filtered = [results[0]]
    
    for i in range(1, len(results)):
        # Se o gap entre este chunk e o anterior for > threshold, parar
        prev_score = results[i-1]["score"]
        curr_score = results[i]["score"]
        if prev_score - curr_score > gap_threshold:
            break
        filtered.append(results[i])
    
    return filtered

# Neste caso: FAQ-38 (0.687) → gap de 0.053 para FAQ-22 (0.634) → cortaria aqui
# Resultado: apenas FAQ-38 enviado ao LLM
```

**Resultado esperado:** Contexto mais limpo. Para este caso, apenas FAQ-38 seria enviado, reduzindo tokens e eliminando risco de confusão com chunks irrelevantes.

---

### Proposta 2 — Adicionar metadado "cobertura_formal" para alertar ausência de documentação normativa

**Problema:** O Anexo B explicita que "nenhum documento formal cobre" o tema de carga danificada. Idealmente, o pipeline deveria detectar essa situação e alertar explicitamente o LLM, facilitando a aplicação da REGRA 6 (tópicos sem cobertura) em conjunto com a REGRA 7.

**Correção no `prompt_builder.py`:** Após a busca, verificar se todos os chunks recuperados são de autoridade "baixa" (FAQ) e, nesse caso, adicionar um alerta no contexto:

```python
def check_formal_coverage(results: list) -> str:
    """Verifica se há pelo menos um chunk de fonte formal nos resultados."""
    has_formal = any(
        r["metadata"].get("authority") in ("maxima", "alta") 
        for r in results
        if r["score"] > 0.5  # considerar apenas chunks com score relevante
    )
    
    if not has_formal:
        return ("\n⚠️ ALERTA DO PIPELINE: Nenhum documento formal (POL, PROC, SLA) "
                "foi recuperado para esta consulta. Todas as fontes disponíveis são "
                "do FAQ-Atendimento (não validado). Aplique REGRA 7 obrigatoriamente.\n")
    return ""
```

**Resultado esperado:** O LLM recebe um sinal explícito de que está operando sem cobertura formal, reforçando a aplicação das REGRAS 6 e 7. Útil para modelos menos capazes que podem não perceber sozinhos que todas as fontes são informais.
