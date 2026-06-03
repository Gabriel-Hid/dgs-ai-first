# Avaliação — Pergunta 4

**Pergunta:** "Frete para 600kg para Manaus?"  
**Data da avaliação:** 02/06/2026  
**Tier do cliente:** DESCONHECIDO  

---

## 1. Chunks Recuperados pelo Pipeline

| # | Chunk | Score | Fonte | Relevância (conforme Anexo B) |
|---|-------|-------|-------|-------------------------------|
| 1 | PROC-042v2-A | 0.454 | PROC-042-v2, seção 2 | ✅ Esperado (fórmula) |
| 2 | PROC-042v2-D | 0.427 | PROC-042-v2, seção 4 | ⚠️ Complementar (condições especiais) |
| 3 | FAQ-27 | 0.426 | FAQ-Atendimento, item 27 | ❌ Irrelevante |
| 4 | FAQ-41 | 0.414 | FAQ-Atendimento, item 41 | ❌ Irrelevante |
| 5 | SLA-2024-A | 0.410 | SLA-2024, seção 1 | ❌ Irrelevante |

**Chunk ausente crítico:** PROC-042v2-B (seção 2.1 — multiplicadores regionais: Norte = 1.8) **NÃO FOI RECUPERADO**. Conforme gabarito do Anexo B, este chunk é OBRIGATÓRIO para esta query.

**Impacto:** Sem o multiplicador regional, é impossível calcular o frete. A resposta fica incompleta.

---

## 2. Resposta Gerada

```
[RESPOSTA DIRETA]
Para uma carga de 600kg com destino a Manaus (região Norte), aplica-se o frete especial
com a seguinte fórmula (Fonte: PROC-042-v2, seção 2):

Valor do frete = Valor base × Multiplicador regional (Norte) × Fator de peso (1.0)

O fator de peso para 600kg é 1.0 (faixa de 500kg a 1.000kg).

[DETALHAMENTO]
⚠️ ATENÇÃO: O multiplicador regional para a região Norte não está disponível nos
documentos recuperados para esta consulta. O chunk com a tabela de multiplicadores
regionais (PROC-042-v2, seção 2.1) não foi incluído no contexto.

O Valor base corresponde à tarifa publicada na tabela mensal de fretes
(Fonte: PROC-042-v2, seção 2).

[FONTE(S)]
📋 PROC-042-v2, seção 2
❌ NÃO ENCONTRADO: Multiplicador regional para Norte (esperado em PROC-042-v2, seção 2.1)

[AÇÃO RECOMENDADA]
↗️ Consulte a tabela de multiplicadores regionais (PROC-042-v2, seção 2.1) ou confirme
com o supervisor o valor do multiplicador para a região Norte antes de informar ao cliente.
```

---

## 3. Avaliação da Resposta

### 3.1. Está correta?

| Afirmação | Verificação contra documentação | Resultado |
|-----------|---------------------------------|-----------|
| Frete especial aplica-se a cargas acima de 500kg | PROC-042-v2, seção 2 | ✅ Correto (600kg > 500kg) |
| Fórmula: Valor base × Multiplicador regional × Fator de peso | PROC-042-v2, seção 2 | ✅ Correto |
| Fator de peso 1.0 para 500-1000kg | PROC-042-v2, seção 2 | ✅ Correto (600kg está nessa faixa) |
| Multiplicador regional não disponível no contexto | Verificação dos chunks | ✅ Correto (PROC-042v2-B ausente) |
| Não inventou o valor do multiplicador | REGRA 2 | ✅ Correto — respeitou proibição de invenção |

**Resultado: ✅ CORRETA** — informações disponíveis foram usadas corretamente; informação ausente foi devidamente sinalizada sem invenção.

### 3.2. Citou fonte?

| Informação | Citação | Formato correto? |
|------------|---------|------------------|
| Fórmula de cálculo | "(Fonte: PROC-042-v2, seção 2)" | ✅ Sim |
| Fator de peso | Implícita na mesma fonte | ✅ Sim |
| Multiplicador ausente | "❌ NÃO ENCONTRADO: esperado em PROC-042-v2, seção 2.1" | ✅ Sim |

**Resultado: ✅ COMPLETA** — citações corretas e indicação precisa do que está ausente.

### 3.3. Respeitou guardrails?

| Guardrail | Cumprido? | Observação |
|-----------|-----------|------------|
| REGRA 1 — Citação obrigatória | ✅ Sim | Fonte citada para dados disponíveis |
| REGRA 2 — Proibição de invenção | ✅ Sim | **NÃO inventou** o multiplicador Norte (1.8). Declarou que não encontrou. |
| REGRA 3 — Informação não encontrada | ✅ Sim | Informou claramente, indicou documento esperado, orientou escalar |
| REGRA 7 — FAQ com alerta | ✅ N/A | Não utilizou nenhum chunk FAQ como fonte |
| Formato de resposta | ✅ Sim | Estrutura completa com marcadores |
| Marcadores visuais | ✅ Sim | Usou ⚠️, 📋, ❌ e ↗️ |

**Resultado: ✅ GUARDRAILS RESPEITADOS**

---

## 4. Nota Geral

| Critério | Nota (1-5) | Justificativa |
|----------|------------|---------------|
| Corretude factual | 5/5 | Nenhum dado incorreto; ausência devidamente sinalizada |
| Citação de fontes | 5/5 | Formato correto; info ausente identificada com documento esperado |
| Guardrails | 5/5 | REGRA 2 (não inventar) e REGRA 3 (não encontrado) aplicadas perfeitamente |
| Formato | 5/5 | Estrutura e marcadores corretos |
| Utilidade para o atendente | 3/5 | Resposta incompleta — atendente não consegue dar valor ao cliente |

**Nota Final: 4.6 / 5.0**

> **Nota:** A nota reflete que a resposta está tecnicamente perfeita quanto a guardrails, mas é funcionalmente incompleta para o atendente. O problema é do **pipeline de retrieval**, não do LLM.

---

## 5. Análise do Retrieval — FALHA CRÍTICA

| Aspecto | Avaliação |
|---------|-----------|
| Chunks obrigatórios presentes? | ❌ PROC-042v2-B (multiplicadores) **NÃO recuperado** |
| Chunks complementares? | ⚠️ PROC-042v2-A (fórmula) presente, mas sem multiplicadores é inútil |
| Chunks irrelevantes? | ❌ FAQ-27, FAQ-41 e SLA-2024-A são completamente irrelevantes |
| Eficiência do Top-K | ❌ Apenas 1-2 de 5 chunks são relevantes |
| Score máximo | ⚠️ 0.454 é baixo — indica que a query "Frete para 600kg para Manaus?" tem baixa similaridade semântica com os chunks |

**Diagnóstico:** A query contém "Manaus" (nome de cidade), mas o chunk PROC-042v2-B usa "Norte" (nome de região). O modelo de embedding não fez a associação geográfica Manaus → Norte. Além disso, "frete" e "600kg" são termos genéricos que atraem chunks diversos.

---

## 6. Propostas de Correção

### Proposta 1 — Enriquecer chunk PROC-042v2-B com nomes de cidades/estados das regiões

**Problema:** O chunk PROC-042v2-B contém "Norte 1.8, Nordeste 1.5, Centro-Oeste 1.4..." mas não menciona cidades ou estados. Queries com "Manaus", "Belém", "Porto Velho" não terão similaridade semântica com o termo "Norte".

**Correção no `ingest.py`:** Adicionar enriquecimento geográfico ao chunk:

```python
# Enriquecer PROC-042v2-B com exemplos de cidades/estados por região:
enrichment = """
Palavras-chave: multiplicador regional, frete por região, tabela multiplicador
Norte (AM, PA, RO, RR, AP, AC, TO, Manaus, Belém, Porto Velho): 1.8
Nordeste (BA, SE, AL, PE, PB, RN, CE, PI, MA, Salvador, Recife, Fortaleza): 1.5
Centro-Oeste (GO, MT, MS, DF, Goiânia, Cuiabá, Campo Grande, Brasília): 1.4
Sudeste (SP, RJ, MG, ES, São Paulo, Rio de Janeiro, Belo Horizonte): 1.1
Sul (PR, SC, RS, Curitiba, Florianópolis, Porto Alegre): 1.3
"""
```

**Resultado esperado:** Queries com nomes de cidades ("Manaus", "Salvador", "Curitiba") passam a ter alta similaridade com PROC-042v2-B, garantindo recuperação do multiplicador correto.

---

### Proposta 2 — Implementar expansão de query com sinônimos geográficos

**Problema:** O embedding model (all-MiniLM-L6-v2) não possui conhecimento geográfico suficiente para associar "Manaus" → "Norte" → multiplicador 1.8. A busca vetorial pura falha para queries com termos específicos que precisam de mapeamento semântico.

**Correção no `search.py`:** Implementar pré-processamento de query com expansão geográfica:

```python
# Mapeamento de cidades/estados para regiões
GEOGRAPHIC_EXPANSION = {
    "manaus": "Norte", "belém": "Norte", "porto velho": "Norte",
    "salvador": "Nordeste", "recife": "Nordeste", "fortaleza": "Nordeste",
    "são paulo": "Sudeste", "rio de janeiro": "Sudeste", "belo horizonte": "Sudeste",
    "curitiba": "Sul", "porto alegre": "Sul", "florianópolis": "Sul",
    "goiânia": "Centro-Oeste", "brasília": "Centro-Oeste", "cuiabá": "Centro-Oeste",
    # + estados (AM, PA, SP, RJ, etc.)
}

def expand_query(query: str) -> str:
    """Expande query adicionando nome da região quando detecta cidade/estado."""
    query_lower = query.lower()
    for city, region in GEOGRAPHIC_EXPANSION.items():
        if city in query_lower:
            return f"{query} região {region} multiplicador regional"
    return query
```

**Resultado esperado:** A query "Frete para 600kg para Manaus?" é expandida para "Frete para 600kg para Manaus? região Norte multiplicador regional", aumentando drasticamente a similaridade com PROC-042v2-B.
