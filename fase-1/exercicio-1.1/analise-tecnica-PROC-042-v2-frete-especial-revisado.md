# Análise Técnica RAG — PROC-042-v2-frete-especial-revisado.md

**Fonte analisada:** PROC-042-v2 — Procedimento de Cálculo de Frete Especial Revisado (v2.0, 10/11/2023)  
**Data da análise:** 2026-05-28  
**Contexto do projeto:** Pipeline RAG para assistente de atendimento NovaTech (GPT-4o, Azure AI Search)

---

## 1. Estimativa de Tamanho em Tokens

### 1.1. Tamanho do documento individual

| Seção                                      | Palavras (est.) | Tokens (÷ 0,75) |
|--------------------------------------------|-----------------|-----------------|
| Cabeçalho + metadados (incluindo alerta de status) | ~55   | ~73             |
| Seção 1 — Objetivo (com nota de revisão)   | ~40             | ~53             |
| Seção 2 — Fórmula de cálculo               | ~85             | ~113            |
| Seção 2.1 — Tabela multiplicadores atualizados | ~45        | ~60             |
| Seção 3 — Prazo de entrega (+3 dias)       | ~40             | ~53             |
| Seção 4 — Condições especiais (c/ desconto automático) | ~80 | ~107          |
| Seção 5 — Disposições transitórias         | ~55             | ~73             |
| **Total do documento**                     | **~400**        | **~533**        |

> Regra aplicada: 1 token ≈ 0,75 palavras (padrão OpenAI/tiktoken para português)

### 1.2. Estimativa do corpus completo (base NovaTech)

| Tipo de documento           | Volume       | Palavras médias  | Total palavras  | Total tokens    |
|-----------------------------|--------------|------------------|-----------------|-----------------|
| PDFs                        | 800 docs     | 10 pág × 300 pal | 2.400.000       | 3.200.000       |
| Páginas wiki                | 400 páginas  | 1.500 pal/página | 600.000         | 800.000         |
| Planilhas                   | 50 arquivos  | ~1.000 pal equiv.| 50.000          | 66.667          |
| **Total estimado**          |              |                  | **3.050.000**   | **~4.067.000**  |

> O corpus completo tem ~4 milhões de tokens — o pipeline deve recuperar seletivamente os poucos chunks relevantes de ~4.067 chunks totais para cada query.

---

## 2. Análise de Orçamento de Contexto

### 2.1. Distribuição da janela de 128k tokens (GPT-4o)

| Slot                                      | Tokens alocados | % da janela |
|-------------------------------------------|-----------------|-------------|
| System prompt + instruções do assistente  | ~2.000          | 1,6%        |
| Query do usuário (pergunta)               | ~200            | 0,2%        |
| Buffer para resposta gerada               | ~1.000          | 0,8%        |
| **Disponível para chunks recuperados**    | **~124.800**    | **97,5%**   |

### 2.2. Capacidade máxima teórica de chunks

```
124.800 tokens disponíveis ÷ 500 tokens/chunk = 249 chunks por query
```

**Isso representa ~6,1% do corpus total** (~249 de ~4.067 chunks equivalentes).

### 2.3. Análise do orçamento em relação ao conflito de versões

A PROC-042-v2 é a versão **preferida** para chamados atuais, mas o orçamento de contexto apresenta um problema específico: como garantir que apenas os chunks v2 — e não os v1 — ocupem o contexto disponível?

**Cenário de ocupação do contexto sem controle de versão:**

```
Query: "qual o multiplicador para o Norte para uma carga de 800kg?"

Contexto montado (sem filtro de versão):
[PROC-042v2-B: Norte = 1.8]     ← score 0.92 (match perfeito)
[PROC-042v1-B: Norte = 1.6]     ← score 0.89 (alta similaridade)
[PROC-042v2-A: fórmula v2]      ← score 0.85
[PROC-042v1-A: fórmula v1]      ← score 0.83 (ainda recuperado!)
...

Tokens ocupados apenas por conteúdo conflitante: ~320 tokens
Tokens úteis (v2 apenas): ~200 tokens
Tokens "poluindo" o contexto (v1): ~120 tokens
```

O efeito "Lost in the Middle" agrava isso: se os chunks v1 ficarem no meio do contexto, o LLM pode não perceber que são de versão diferente e misturar os valores.

### 2.4. Recomendação de Top-K e orçamento para este documento

| Estratégia                    | Chunks           | Tokens  | Risco        |
|-------------------------------|-----------------|---------|--------------|
| Sem filtro de versão          | 5 v2 + 4 v1     | ~4.500  | Alto         |
| Com filtro `source = PROC-042-v2` | 5 v2 apenas | ~2.500  | Baixo        |
| Com boost score para v2       | 5 v2 + 0-1 v1   | ~2.500  | Controlado   |

> **Recomendação:** Usar **filtro de metadado** no Azure AI Search (`source_document = PROC-042-v2`) como pré-filtro antes do ranqueamento por similaridade. Isso garante que o orçamento de contexto seja ocupado exclusivamente por dados corretos.

---

## 3. Recomendações de Estratégia de Chunking

### 3.1. Características do documento que impactam o chunking

| Característica                             | Impacto no RAG                                                      |
|--------------------------------------------|---------------------------------------------------------------------|
| Versão atual (de fato, não oficialmente)   | Alta prioridade de recuperação para chamados ≥ 01/12/2023           |
| Tabela de multiplicadores atualizada       | Valores diferentes dos v1 — chunk deve ser identificável            |
| Seção 5 (Disposições transitórias)         | Lógica condicional (antes/depois de 01/12/2023) — chunk crítico     |
| Desconto automático por volume (sec. 4)    | Regra de negócio nova vs v1 — manter como unidade                   |
| Fórmula idêntica à v1 (mas parâmetros ≠)  | Alta similaridade semântica com v1 — risco de deduplicação indevida |
| Nota sobre PROC-043 em revisão             | Dependência externa instável — metadado de caveat                   |

### 3.2. Estratégia recomendada: Chunking por Seção com Metadado de Versão como Chave Primária

**Template de chunk:**
```
[FONTE: PROC-042 | VERSÃO: 2.0 | DATA: 10/11/2023 | STATUS: ✅ VERSÃO ATUAL]
[Aplica-se a: chamados abertos a partir de 01/12/2023 | Cargas: acima de 500kg]
[Tópico: {fórmula / multiplicadores-atualizados / prazo / desconto-volume / transição}]

{conteúdo da seção}
```

> A marcação `STATUS: ✅ VERSÃO ATUAL` deve ser explícita e contrastante com o `STATUS: ⚠️ SUBSTITUÍDO` da v1. Isso dá ao LLM informação explícita para resolver o conflito quando ambas versões aparecerem no contexto.

### 3.3. Chunking recomendado

| Chunk ID        | Seção               | Conteúdo                                                   | Tokens (est.) | Prioridade |
|-----------------|---------------------|-------------------------------------------------------------|---------------|------------|
| PROC-042v2-A    | 2 (fórmula + pesos) | Fórmula + Fatores de peso atualizados (1.0/1.15/1.4)       | ~130          | **Alta**   |
| PROC-042v2-B    | 2.1                 | Tabela multiplicadores regionais v2 (Sul 1.3 ... Norte 1.8) | ~85          | **Alta**   |
| PROC-042v2-C    | 3                   | Prazo: +3 dias úteis (vs +2 da v1)                         | ~65           | **Alta**   |
| PROC-042v2-D    | 4 (descontos)       | Desconto automático ≥8 fretes (5%) e ≥15 fretes (10%)      | ~110          | **Alta**   |
| PROC-042v2-E    | 5 (transição)       | Regra: v1 para chamados pré-01/12/2023; v2 para novos      | ~90           | **Crítica**|

### 3.4. Importância crítica do Chunk PROC-042v2-E (Disposições Transitórias)

Este chunk contém a **regra de decisão** sobre qual versão usar. Sem ele no contexto, o LLM não tem base para responder perguntas como "qual versão aplico para este cliente que abriu chamado em novembro/2023?".

**Query típica que exige este chunk:**
- "O cliente abriu chamado em 20/11/2023 — uso qual tabela de multiplicadores?"
- "Chamado ainda em aberto desde novembro, qual fórmula usar?"

**Risco sem chunk de transição:**
- LLM usa v2 para tudo (erro: contratos legados devem usar v1)
- LLM usa v1 para tudo (erro: novos chamados devem usar v2)
- LLM responde sem clareza sobre qual usar (inutilizável pelo atendente)

### 3.5. Análise do efeito "Lost in the Middle" para queries de cálculo de frete

Perguntas de cálculo de frete são **numéricas e precisas** — o atendente precisa do valor exato do multiplicador, não de uma aproximação. Isso torna o efeito "Lost in the Middle" especialmente danoso:

```
Exemplo de query: "Quanto custa frete especial para 2000kg para o Nordeste?"

Contexto montado (com lost in the middle):
[INÍCIO] PROC-042v2-A: fórmula = base × multiplicador × 1.15  (atenção alta)
[MEIO]   PROC-042v2-B: Nordeste = 1.5                         (atenção BAIXA) ← valor crítico
[MEIO]   PROC-042v1-B: Nordeste = 1.4                         (atenção BAIXA) ← valor errado
[FIM]    PROC-042v2-D: desconto volume                        (atenção alta)

→ LLM com "lost in the middle" pode usar Nordeste = 1.4 (v1) em vez de 1.5 (v2)
→ Cotação ~7% menor que o correto
```

**Mitigação:** Construir o prompt RAG posicionando o chunk de multiplicadores regionais (PROC-042v2-B) **sempre no início** do contexto, imediatamente após o system prompt.

### 3.6. Considerações sobre Desafios Técnicos do Projeto

| Desafio técnico      | Relevância para PROC-042-v2                          | Solução                                        |
|----------------------|------------------------------------------------------|------------------------------------------------|
| PDFs escaneados (OCR)| Tabelas de multiplicadores podem ter dígitos trocados (ex: 1.8 → 1.6) | Validação numérica pós-OCR contra tabela de referência |
| Planilhas (50 arquivos) | Tabela mensal de fretes (`frete-base-AAAAMM.xlsx`) é referenciada neste documento | Ingestão separada das planilhas com link para este PROC |
| Fluxogramas em imagens | Processo de aprovação ≥5000kg pode estar em diagrama | Extração multi-modal |
| Versões concorrentes | **Este é o contexto exato** — v1 e v2 no mesmo índice | Filtro de metadado `version_status` no retrieval |

### 3.7. Riscos específicos deste documento no pipeline RAG

| Risco                          | Descrição                                                              | Mitigação                                          |
|-------------------------------|------------------------------------------------------------------------|----------------------------------------------------|
| Confusão v1/v2 no contexto    | Alta similaridade semântica faz retrieval recuperar ambas versões      | Filtro de metadado `source = PROC-042-v2` + boost  |
| Chunk de transição não recuperado | Sem seção 5, LLM não sabe qual versão aplicar para chamados legados | Indexar seção 5 com keywords de data e "chamado antigo" |
| Tabela serializada incorretamente | OCR de PDF pode serializar tabela como texto plano sem estrutura     | Template de serialização padronizado para tabelas  |
| FAQ-08 contraditório          | FAQ diz "use v2, mas cliente pode estar no contrato antigo" — ambíguo | FAQ deve ter prioridade menor que PROC-042v2       |
| Desconto automático vs negociado | v1 diz "negocie com Comercial"; v2 diz "automático" — diferença real | Chunk v2-D deve explicitar que substitui regra v1  |

---

## Resumo Executivo

A PROC-042-v2 é o documento de **máxima autoridade para cálculo de frete especial em chamados atuais** (a partir de 01/12/2023). Com ~533 tokens, gera 5 chunks de alta prioridade, incluindo um chunk de disposições transitórias que é crítico para resolver ambiguidades de versão. O maior desafio RAG é garantir que esta versão **prevaleça sobre a v1 no retrieval**, usando metadados explícitos de `VERSION: 2.0 / STATUS: ATUAL` em todos os chunks, filtros de busca por fonte, e posicionamento preferencial no início do contexto. O chunk PROC-042v2-E (transição) deve ter alta cobertura semântica para ser recuperado em queries sobre chamados históricos.

---

## Feedback Técnico — Revisão Crítica da Análise

> **Revisão por:** Engenheiro de IA (RAG)  
> **Data:** 2026-05-28  
> **Escopo:** Identificação de estimativas otimistas, pontos fracos e riscos não considerados na primeira versão desta análise.

---

### F.1. Estimativas Otimistas Demais

#### F.1.1. Chunk PROC-042v2-E (Disposições Transitórias) como ferramenta de resolução de versão — premissa expirada
O chunk de disposições transitórias referencia a data de corte **01/12/2023** como ponto de decisão entre v1 e v2. Em maio de 2026, essa data está há mais de 2 anos no passado. O valor prático desse chunk para resolver conflitos de versão **diminui a cada mês**: em operação atual, todos os chamados são posteriores a 01/12/2023 e deveriam usar a v2 por definição. A análise confere importância elevada a esse chunk como se o período de transição ainda fosse relevante, quando na prática ele já deveria ter sido encerrado administrativamente. O risco real é que esse chunk pode **confundir o LLM** ao trazer um contexto de transição anacrônico para queries modernas.

#### F.1.2. Boost de score para v2 mencionado sem parâmetros
A análise recomenda "boost score para v2" como alternativa ao filtro de metadado, sem especificar o valor do boost. No Azure AI Search, o boost é configurado via `featuresMode` e `scoringProfiles`. Um boost de +0.05 pode ser insuficiente se a similaridade semântica da v1 for apenas 0.03 menor que a da v2. Um boost de +0.3 pode fazer chunks de v2 com baixa relevância aparecerem à frente de chunks de outros documentos mais relevantes. A **calibração do boost precisa de testes empíricos** e o valor correto depende da distribuição de scores do corpus específico — não é uma configuração que se define sem dados.

---

### F.2. Pontos Fracos da Análise

#### F.2.1. Tabela base de fretes (`frete-base-AAAAMM.xlsx`) — dependência crítica não endereçada
A fórmula de cálculo do frete especial requer o **Valor base** da tabela mensal de fretes (`\\novatech-fs\comercial\tabelas\frete-base-AAAAMM.xlsx`). A análise menciona essa dependência em 3.6 ("Ingestão separada das planilhas com link para este PROC"), mas não discute a implicação crítica: essa planilha **muda mensalmente**. Se o pipeline re-indexar a planilha todo mês, como garantir que a versão do mês anterior seja retirada do índice? E se o assistente precisar calcular um frete retroativo para o mês anterior? A gestão de versões mensais de uma planilha de referência é um problema de engenharia de dados não trivial — subestimado ao ser tratado apenas como "ingestão separada".

#### F.2.2. PROC-043 em revisão cria risco de desatualização em cascata
A seção 4 da PROC-042-v2 referencia PROC-043 (Frete de Cargas Perigosas) com a nota de que está "em processo de revisão pelo Compliance". Se a PROC-043 for atualizada, qualquer resposta do assistente que combine frete especial + carga perigosa pode ficar **desatualizada sem aviso** — o assistente usaria v2 do PROC-042 (correto) mas com uma premissa de PROC-043 obsoleta. A análise registra a nota de caveat no chunk mas não mapeia o risco de que um documento externo relevante seja modificado sem re-trigger da análise de impacto no pipeline.

#### F.2.3. Filtro de metadado `source_document = PROC-042-v2` requer arquitetura de índice definida
A análise recomenda filtro de metadado como solução primária, mas não discute **como esse metadado é populado no índice do Azure AI Search**. Se os documentos forem ingeridos a partir do SharePoint via conector padrão, o metadado de `source_document` precisa ser mapeado de algum campo do SharePoint (nome do arquivo, caminho, tag de metadado). Se os documentos forem carregados manualmente ou via script, o mapeamento precisa ser implementado no pipeline de ingestão. A análise assume que o metadado estará disponível sem discutir **de onde vem** — e falhas nessa etapa de ingestão tornam o filtro silenciosamente ineficaz.

#### F.2.4. Seção de descontos de volume (v2-D) conflita com FAQ-45 e precisa de resolução explícita
O FAQ-45 diz "Para clientes com mais de 10 fretes especiais por mês, existe desconto automático na tabela (veja PROC-042)." Isso está errado: a v2 define ≥8 fretes (não 10) como threshold. O FAQ-45 refere-se implicitamente à v1, que usava ">10 fretes". A análise identifica o conflito no risco "FAQ-08 contraditório", mas **FAQ-45 é um conflito diferente e mais específico** (threshold numérico errado). Um atendente que perguntar "meu cliente tem 9 fretes por mês, tem desconto?" receberá respostas conflitantes dependendo de qual chunk é recuperado. Este caso de uso específico não está nos exemplos de query da análise.

---

### F.3. Riscos Não Considerados

#### F.3.1. Ausência de estratégia para calibração e teste dos filtros de retrieval
A análise propõe filtros de metadado, boosts e posicionamento de chunks como mitigações, mas não propõe **como testar se essas mitigações funcionam**. Um evaluation set específico para queries de frete com casos de borda (chamados pré-2024, múltiplas regiões, pesos na borda das faixas como exatamente 1.000 kg ou 3.000 kg) é necessário para validar o comportamento do pipeline antes de produção. Sem testes, as mitigações podem ter falhas silenciosas descobertas apenas quando um atendente fornecer uma cotação errada a um cliente.

#### F.3.2. Chunks numéricos são particularmente vulneráveis a desvios de atenção no LLM
A análise discute "lost in the middle" para a tabela de multiplicadores, mas não menciona um risco adicional: LLMs frequentemente cometem **erros aritméticos ou de leitura de tabela** mesmo quando o dado correto está no contexto. O cálculo `Valor base × 1.5 × 1.4` (base × multiplicador regional Nordeste × fator peso >3000kg) requer que o LLM identifique corretamente dois valores numéricos de dois chunks diferentes e os multiplique. Erros de arredondamento, confusão de campos da tabela ou uso do fator de peso errado para a faixa de kg são falhas que ocorrem independentemente do "lost in the middle". A solução não é apenas garantir que o chunk seja lido — é validar a capacidade do LLM de executar o cálculo corretamente, o que exige testes de QA específicos para cálculos numéricos.

#### F.3.3. Aprovação prévia para cargas acima de 5.000 kg não tem fluxo automatizado
A seção 4 exige "aprovação prévia do gerente de operações regional" para cargas acima de 5.000 kg. O assistente RAG não pode executar um fluxo de aprovação — pode apenas orientar o atendente. O risco é que o assistente responda com os multiplicadores calculados para uma carga de 6.000 kg sem sinalizar adequadamente que **o cálculo é condicional a uma aprovação que ainda não foi obtida**. Se o atendente usar o valor calculado como cotação final antes da aprovação, cria-se um compromisso informal não autorizado. O chunk PROC-042v2-A ou v2-D deve incluir essa condicionalidade de forma destacada.
