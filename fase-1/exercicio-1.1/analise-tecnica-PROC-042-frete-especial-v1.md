# Análise Técnica RAG — PROC-042-frete-especial-v1.md

**Fonte analisada:** PROC-042 — Procedimento de Cálculo de Frete Especial (v1.0, 03/03/2023)  
**Data da análise:** 2026-05-28  
**Contexto do projeto:** Pipeline RAG para assistente de atendimento NovaTech (GPT-4o, Azure AI Search)

---

## 1. Estimativa de Tamanho em Tokens

### 1.1. Tamanho do documento individual

| Seção                                    | Palavras (est.) | Tokens (÷ 0,75) |
|------------------------------------------|-----------------|-----------------|
| Cabeçalho + metadados (incluindo alerta de status) | ~50   | ~67             |
| Seção 1 — Objetivo                       | ~30             | ~40             |
| Seção 2 — Fórmula de cálculo             | ~80             | ~107            |
| Seção 2.1 — Tabela multiplicadores (5 linhas) | ~40        | ~53             |
| Seção 3 — Prazo de entrega               | ~30             | ~40             |
| Seção 4 — Condições especiais            | ~60             | ~80             |
| **Total do documento**                   | **~290**        | **~387**        |

> Regra aplicada: 1 token ≈ 0,75 palavras (padrão OpenAI/tiktoken para português)  
> Tabelas Markdown têm overhead de tokens (~20% adicional por pipes e formatação)

### 1.2. Estimativa do corpus completo (base NovaTech)

| Tipo de documento           | Volume       | Palavras médias  | Total palavras  | Total tokens    |
|-----------------------------|--------------|------------------|-----------------|-----------------|
| PDFs                        | 800 docs     | 10 pág × 300 pal | 2.400.000       | 3.200.000       |
| Páginas wiki                | 400 páginas  | 1.500 pal/página | 600.000         | 800.000         |
| Planilhas                   | 50 arquivos  | ~1.000 pal equiv.| 50.000          | 66.667          |
| **Total estimado**          |              |                  | **3.050.000**   | **~4.067.000**  |

> O corpus completo tem aproximadamente **4 milhões de tokens** — impossível indexar integralmente em uma única query; retrieval vetorial é essencial.

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

### 2.3. O problema central deste documento no orçamento de contexto

A PROC-042-v1 coexiste com a PROC-042-v2 no mesmo índice vetorial. Ambas têm alta similaridade semântica porque descrevem o **mesmo processo** com parâmetros diferentes. Uma query como "qual o multiplicador para o Norte?" pode recuperar chunks de **ambas as versões** dentro do mesmo orçamento de contexto:

```
Cenário problemático de ocupação do contexto:
[PROC-042-v1-B: Norte = 1.6]   ← chunk recuperado
[PROC-042-v2-B: Norte = 1.8]   ← chunk recuperado (alta similaridade semântica)

→ LLM vê dois valores contraditórios e pode:
   (a) usar o mais recente corretamente (ideal)
   (b) fazer média ou escolher aleatoriamente (erro)
   (c) mencionar a contradição sem resolver (confuso para o atendente)
```

**Este é o risco de "Lost in the Middle" mais crítico da base NovaTech:** versões conflitantes de parâmetros numéricos ocupam o contexto simultaneamente, e o LLM pode não priorizar corretamente sem instrução explícita.

### 2.4. Recomendação de Top-K para queries de frete

| Estratégia       | Chunks recuperados | Tokens usados | Risco de conflito v1/v2 |
|------------------|-------------------|---------------|--------------------------|
| Mínimo           | 3                 | ~1.500        | Médio (pode não trazer v2)|
| Recomendado      | 5–8               | ~2.500–4.000  | Alto se sem filtro de versão |
| Com filtro       | 5 (apenas v2)     | ~2.500        | Baixo (versão controlada) |

> **Recomendação crítica:** Implementar filtro de metadado `version_status = deprecated` para excluir PROC-042-v1 do retrieval padrão, ou aplicar boosts de score para chunks de v2.

---

## 3. Recomendações de Estratégia de Chunking

### 3.1. Características do documento que impactam o chunking

| Característica                          | Impacto no RAG                                                   |
|-----------------------------------------|------------------------------------------------------------------|
| Versão obsoleta de fato (não oficialmente) | Sem marcação formal de obsolescência — alto risco de retrieval |
| Tabela de multiplicadores (5 regiões)   | Tabela pequena — manter inteira no mesmo chunk                   |
| Fórmula matemática (3 variáveis)        | Variáveis devem ser explicadas no mesmo chunk que a fórmula      |
| Fatores de peso (3 faixas kg)           | Contexto numérico — chunk junto com a fórmula                    |
| Referência a PROC-043                   | Link externo — metadado de dependência                           |
| Status de coexistência com v2           | Requer metadado explícito de `version_status = deprecated`       |

### 3.2. Estratégia recomendada: Chunking por Seção com Metadado de Versão Obrigatório

**Unidade de chunk:** 1 seção lógica por chunk, com metadados de versão e status

**Template de chunk obrigatório:**
```
[FONTE: PROC-042 | VERSÃO: 1.0 | DATA: 03/03/2023 | STATUS: ⚠️ SUBSTITUÍDO por PROC-042-v2 (10/11/2023)]
[Tipo: Procedimento de frete especial | Aplica-se a: cargas acima de 500kg]

{conteúdo da seção}

⚠️ ATENÇÃO: Use PROC-042-v2 para chamados abertos após 01/12/2023.
Este documento aplica-se apenas a chamados abertos antes de 01/12/2023.
```

> O cabeçalho de obsolescência deve estar em **todo chunk** deste documento, não apenas no chunk de metadados raiz. Isso garante que mesmo que um único chunk seja recuperado isoladamente, o LLM receberá o aviso de versão.

### 3.3. Chunking recomendado

| Chunk ID       | Seção               | Conteúdo                                              | Tokens (est.) | Prioridade de indexação |
|----------------|---------------------|-------------------------------------------------------|---------------|------------------------|
| PROC-042v1-A   | 2 (fórmula + pesos) | Fórmula + Fatores de peso (500kg-1000kg, 1001-3000kg, >3000kg) | ~120  | Baixa (v2 preferida)   |
| PROC-042v1-B   | 2.1                 | Tabela multiplicadores regionais (5 regiões, v1)     | ~80           | **Baixíssima** — contradiz v2 |
| PROC-042v1-C   | 3                   | Prazo: +2 dias úteis                                  | ~60           | Baixa — v2 diz +3 dias |
| PROC-042v1-D   | 4                   | Condições especiais (≥5000kg, desconto ≥10 fretes)   | ~90           | Média — v2 atualiza desconto |

### 3.4. Análise comparativa dos valores divergentes entre v1 e v2

Esta tabela é **central para entender o risco RAG** de manter ambos os documentos no índice:

| Parâmetro               | PROC-042 v1 (este doc) | PROC-042 v2        | Impacto se v1 usado incorretamente |
|-------------------------|------------------------|--------------------|------------------------------------|
| Multiplicador Sul       | 1.2                    | 1.3                | Frete 8,3% mais barato (erro favorável ao cliente) |
| Multiplicador Sudeste   | 1.0                    | 1.1                | Frete 10% mais barato              |
| Multiplicador Centro-Oeste | 1.3                 | 1.4                | Frete 7,7% mais barato             |
| Multiplicador Nordeste  | 1.4                    | 1.5                | Frete 7,1% mais barato             |
| Multiplicador Norte     | 1.6                    | 1.8                | Frete 12,5% mais barato            |
| Fator de peso médio (1001-3000kg) | 1.2         | 1.15               | Frete 4,3% mais caro (erro desfavorável ao cliente) |
| Fator de peso alto (>3000kg) | 1.5             | 1.4                | Frete 7,1% mais caro               |
| Prazo adicional         | +2 dias úteis          | +3 dias úteis      | Expectativa de entrega incorreta   |
| Desconto volume         | >10 fretes/mês (neg.)  | ≥8 fretes/mês (5%); ≥15 (10%) | Perda de desconto ao cliente |

> **Conclusão:** Usar v1 em vez de v2 gera cotações de frete sistematicamente menores para a maioria das regiões, causando perda de receita para a NovaTech ou retrabalho quando o cliente receber a cobrança correta.

### 3.5. Estratégia de tratamento deste documento no pipeline RAG

**Opção A — Manutenção com filtro de período (recomendada):**
- Indexar com metadado `applies_to_period = before_2023-12-01`
- Filtrar retrieval por data de abertura do chamado
- Usar apenas quando o atendente explicitamente mencionar chamado antigo

**Opção B — Deprecação completa:**
- Marcar todos os chunks com `version_status = deprecated`
- Excluir do retrieval padrão
- Manter como referência histórica apenas em queries específicas de auditoria

**Opção C — Não indexar (não recomendada):**
- Risco: perda de contexto para chamados legados (disposições transitórias da v2, seção 5)

### 3.6. Considerações sobre Desafios Técnicos do Projeto

| Desafio técnico      | Relevância para PROC-042-v1            | Solução                                     |
|----------------------|----------------------------------------|---------------------------------------------|
| PDFs escaneados (OCR)| Tabelas de multiplicadores em PDFs originais podem ter erros de OCR nos valores numéricos | Validação pós-OCR de valores numéricos |
| Fluxogramas em imagens| Processo de aprovação ≥5000kg pode estar em fluxograma | GPT-4V para extração de fluxo |
| Tabelas complexas    | Tabela de multiplicadores 5×2 é simples, mas em PDF pode perder formatação | Table extraction dedicada |
| Versões concorrentes | **Este é o caso exato** — PROC-042-v1 vs v2 sem hierarquia formal | Metadado de versão + filtros de retrieval |

---

## Resumo Executivo

A PROC-042-v1 é um documento **de baixa prioridade de recuperação** no estado atual do pipeline, pois foi efetivamente substituída pela v2 para chamados a partir de 01/12/2023. Com ~387 tokens, é o menor documento da base. O principal risco RAG é a **coexistência no índice com a v2**: ambas respondem semanticamente às mesmas queries, mas com valores numéricos divergentes. A mitigação obrigatória é o metadado de status de versão em todos os chunks e um filtro de retrieval baseado em data do chamado. Manter este documento no índice sem controle de versão pode causar cotações de frete incorretas sistematicamente.

---

## Feedback Técnico — Revisão Crítica da Análise

> **Revisão por:** Engenheiro de IA (RAG)  
> **Data:** 2026-05-28  
> **Escopo:** Identificação de estimativas otimistas, pontos fracos e riscos não considerados na primeira versão desta análise.

---

### F.1. Estimativas Otimistas Demais

#### F.1.1. Opção A (filtro por período) pressupõe disponibilidade de metadado de data na query
A Opção A recomenda filtrar retrieval pela data de abertura do chamado (`applies_to_period = before_2023-12-01`). Isso implica que o sistema de RAG tem acesso à data do chamado **como variável de contexto estruturado** no momento da busca. Em um assistente conversacional, o atendente tipicamente digita a pergunta em linguagem natural sem incluir a data do chamado. Extrair a data exige: (a) o atendente informar explicitamente, (b) integração com o sistema de chamados (Azure DevOps) para consulta em tempo real, ou (c) extração de entidade temporal da query com NLP. Nenhuma dessas abordagens é trivial. A análise trata o filtro por período como solução simples, mas sua **implementação real é uma integração de sistema** que precisa ser dimensionada e validada antes de ser adotada.

#### F.1.2. Estimativa de corpus subestima planilhas e overhead de template
Mesma ressalva sistemática das demais análises: 50 planilhas × 1.000 palavras/planilha é 5–15× subestimado. A tabela de fretes base (`frete-base-AAAAMM.xlsx`) mencionada neste documento pode ter centenas de rotas × múltiplas faixas de peso, o que produz muito mais tokens que a estimativa.

---

### F.2. Pontos Fracos da Análise

#### F.2.1. Opção C (não indexar) descartada prematuramente
A análise rejeita "Não indexar" com o argumento de que causaria "perda de contexto para chamados legados". Porém, como identificado em F.1.1, a Opção A (filtro por período) requer integração não trivial. E a Opção B (deprecar com metadado) cria um chunk com conteúdo numérico errado no índice que pode vazar para o LLM se o filtro falhar. A **Opção C pode ser a mais segura operacionalmente**: os chamados abertos antes de 01/12/2023 que ainda estão em processamento (mais de 2 anos depois!) provavelmente são casos tão raros e especializados que merecem consulta manual — não automação via RAG. A análise não quantifica o volume real desses chamados legados, o que seria necessário para justificar a complexidade das Opções A ou B.

#### F.2.2. A data de corte 01/12/2023 está há mais de 2 anos no passado
Em maio de 2026, **praticamente nenhum chamado ativo foi aberto antes de 01/12/2023**. O período de transição da PROC-042-v2 já expirou completamente. A análise discute a convivência de versões como se fosse um cenário presente e relevante, quando na prática a v1 está completamente obsoleta para o fluxo operacional atual. Isso não invalida a recomendação de marcar a v1 como deprecated, mas torna a Opção A (filtro temporal) ainda menos justificável em termos de custo/benefício de implementação.

#### F.2.3. Risco de OCR introduzir erros em valores numéricos — não tratado como risco de alta severidade
A tabela de multiplicadores da PROC-042-v1 contém valores como 1.6, 1.4, 1.3. Um erro de OCR pode transformar `1.6` em `1.0` ou `1.8` — valores que são **válidos em outros contextos** (1.0 é o multiplicador do Sudeste na v1; 1.8 é o multiplicador do Norte na v2). Isso é um erro de OCR quase indetectável por validação semântica. A análise menciona "validação numérica pós-OCR" como solução, mas não detalha *como* essa validação seria feita — contra qual referência? Quem a executa? O risco de erro silencioso de OCR em valores numéricos de tabelas é elevado e merece um protocolo específico de QA.

#### F.2.4. Sem análise de impacto para o caso de desconto de volume
A v1 define desconto de volume como ">10 fretes/mês → negociar com Comercial", enquanto a v2 define regras automáticas (≥8 fretes/mês = 5%; ≥15 = 10%). Um atendente que use dados da v1 para responder a um cliente com 9 fretes/mês pode dizer "você não tem desconto automático" (correto para v1) quando na verdade o cliente tem direito a 5% (correto para v2). Este erro não é apenas financeiro para a NovaTech — é um **erro de atendimento que prejudica o cliente** e pode gerar reclamações. A análise lista a diferença na tabela comparativa mas não eleva a gravidade desse caso de uso específico.

---

### F.3. Riscos Não Considerados

#### F.3.1. Ausência de mecanismo de detecção de "qual versão usar?" em linguagem natural
Se um atendente digitar "qual o multiplicador para o Norte?", sem mencionar datas, a query é semanticamente idêntica para ambas as versões. O LLM precisaria inferir do contexto conversacional qual versão aplicar. Sem o chunk PROC-042v2-E no contexto (disposições transitórias), o LLM não tem como decidir. E mesmo com ele, a regra de decisão requer que o atendente **saiba a data de abertura do chamado** e a forneça na conversa — informação que frequentemente não está disponível no início de uma interação de suporte.

#### F.3.2. Ambiguidade semântica entre v1 e v2 não é resolúvel apenas por metadados no chunk
A análise propõe que o cabeçalho `STATUS: ⚠️ SUBSTITUÍDO` em todos os chunks da v1 fará o LLM ignorá-los em favor da v2. Isso é uma **suposição não testada**: LLMs podem dar peso diferente a indicadores textuais de status dependendo do contexto. Se a query for suficientemente similar ao conteúdo da v1 e o score de similaridade for alto o suficiente para colocar o chunk da v1 no início do contexto, o LLM pode usar o valor errado mesmo com o aviso de substituição. A única mitigação confiável é **exclusão por filtro no retrieval**, não instrução textual no chunk.

#### F.3.3. O pipeline atual não tem dono responsável pela versão ativa
O Anexo A documenta explicitamente que nenhum dos dois documentos está marcado como obsoleto no SharePoint da NovaTech. Isso significa que o problema de coexistência de versões é um **problema de governança documental** que precede o pipeline de RAG. Qualquer solução técnica no pipeline (filtros, metadados, boosts) é um workaround para um problema que a área de Documentação/Compliance deveria resolver. A análise deveria elevar essa dependência como um **risco de pré-requisito**: sem a NovaTech formalizar qual versão está ativa, qualquer solução técnica é frágil e pode ser contornada por um futuro upload de documento sem metadados corretos.
