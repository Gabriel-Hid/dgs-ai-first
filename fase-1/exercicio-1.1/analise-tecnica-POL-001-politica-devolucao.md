# Análise Técnica RAG — POL-001-politica-devolucao.md

**Fonte analisada:** POL-001 — Política de Devolução de Mercadorias (v3.1, 15/01/2024)  
**Data da análise:** 2026-05-28  
**Contexto do projeto:** Pipeline RAG para assistente de atendimento NovaTech (GPT-4o, Azure AI Search)

---

## 1. Estimativa de Tamanho em Tokens

### 1.1. Tamanho do documento individual

| Seção                                  | Palavras (est.) | Tokens (÷ 0,75) |
|----------------------------------------|-----------------|-----------------|
| Cabeçalho + metadados                  | ~30             | ~40             |
| Seção 1 — Objetivo                     | ~50             | ~67             |
| Seção 2 — Escopo                       | ~45             | ~60             |
| Seção 3.1 — Prazo geral                | ~40             | ~53             |
| Seção 3.2 — Exceções (lista perigosas) | ~130            | ~173            |
| Seção 3.3 — Procedimento (5 passos)    | ~100            | ~133            |
| Seção 3.4 — Devoluções parciais        | ~55             | ~73             |
| Seção 3.5 — Custos                     | ~70             | ~93             |
| **Total do documento**                 | **~520**        | **~693**        |

> Regra aplicada: 1 token ≈ 0,75 palavras (padrão OpenAI/tiktoken para português)

### 1.2. Estimativa do corpus completo (base NovaTech)

| Tipo de documento           | Volume       | Palavras médias  | Total palavras  | Total tokens    |
|-----------------------------|--------------|------------------|-----------------|-----------------|
| PDFs                        | 800 docs     | 10 pág × 300 pal | 2.400.000       | 3.200.000       |
| Páginas wiki                | 400 páginas  | 1.500 pal/página | 600.000         | 800.000         |
| Planilhas                   | 50 arquivos  | ~1.000 pal equiv.| 50.000          | 66.667          |
| **Total estimado**          |              |                  | **3.050.000**   | **~4.067.000**  |

> O corpus completo tem aproximadamente **4 milhões de tokens** — ~31× a janela do GPT-4o (128k). Todo o corpus não cabe em uma única query; retrieval seletivo é obrigatório.

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

### 2.3. Impacto do efeito "Lost in the Middle" na POL-001

A POL-001 contém **regras críticas com exceções explícitas** (seção 3.2). O efeito "lost in the middle" é particularmente perigoso aqui porque:

- Se o chunk POL-001-B (exceções: cargas perigosas não elegíveis) cair no meio do contexto, o LLM pode ignorá-lo e responder como se toda carga fosse elegível para devolução.
- A pergunta "posso devolver?" tem resposta diferente dependendo do **tipo de carga** — informação contida em chunks separados que precisam ser consultados juntos.

```
Contexto montado incorretamente:
[POL-001-A: prazo 7 dias]  ← início (alta atenção)
[POL-001-C: procedimento]  ← meio (baixa atenção)
[POL-001-B: exceções]      ← meio (baixa atenção) ← RISCO: regra crítica ignorada
[outros chunks...]
[POL-001-D: custos]        ← fim (atenção recuperada)

→ LLM responde: "pode devolver em 7 dias" sem mencionar exceções de carga perigosa
```

### 2.4. Recomendação de Top-K para este documento

| Estratégia       | Chunks recuperados | Tokens usados | Qualidade esperada |
|------------------|-------------------|---------------|--------------------|
| Mínimo           | 3                 | ~1.500        | Alta (query simples)|
| Recomendado      | 5–8               | ~2.500–4.000  | Alta               |
| Limite prático   | 15                | ~7.500        | Boa (risco baixo)  |

> Para perguntas sobre devolução, recuperar sempre os chunks POL-001-A e POL-001-B juntos (prazo + exceções) é obrigatório para evitar respostas incompletas e potencialmente prejudiciais.

---

## 3. Recomendações de Estratégia de Chunking

### 3.1. Características do documento que impactam o chunking

| Característica                    | Impacto no RAG                                                  |
|-----------------------------------|-----------------------------------------------------------------|
| Documento normativo formal (v3.1) | Alta autoridade — deve superar FAQ em ranqueamento             |
| Regras com exceções explícitas    | Chunks de regra e exceção devem ser recuperados juntos          |
| Procedimento em 5 passos (3.3)    | Lista ordenada — dividir os passos destrói o sentido            |
| Referências cruzadas (PROC-088)   | Metadado de dependência para queries sobre carga em trânsito   |
| Tabela de custos (3.5)            | Três cenários mutuamente exclusivos — manter juntos             |

### 3.2. Estratégia recomendada: Chunking Semântico por Seção com Pareamento Obrigatório

**Unidade de chunk:** 1 seção lógica por chunk, com metadados de contexto normativo

**Template de chunk:**
```
[FONTE: POL-001 | VERSÃO: 3.1 | DATA: 15/01/2024 | TIPO: Política normativa | AUTORIDADE: Alta]
[Seção: {número e título da seção}]
[Tópico: {devolução / prazo / exceção / procedimento / custo}]

{conteúdo da seção}

[Referências cruzadas: {lista de docs citados nesta seção, se houver}]
```

**Chunking recomendado:**

| Chunk ID     | Seção               | Conteúdo                                          | Tokens (est.) | Nota de pareamento             |
|--------------|---------------------|---------------------------------------------------|---------------|-------------------------------|
| POL-001-A    | 3.1                 | Prazo de 7 dias úteis                             | ~70           | Sempre recuperar com POL-001-B |
| POL-001-B    | 3.2                 | Exceções (carga perigosa, refrigerada, lacre)     | ~180          | Sempre recuperar com POL-001-A |
| POL-001-C    | 3.3                 | Procedimento passo-a-passo (5 etapas inteiras)    | ~140          | Manter como unidade indivisível|
| POL-001-D    | 3.4                 | Devoluções parciais                               | ~80           | Independente                  |
| POL-001-E    | 3.5                 | Custos (3 cenários)                               | ~100          | Manter como unidade indivisível|

> **Regra crítica:** Os 5 passos da seção 3.3 **não devem ser divididos em chunks separados**. Se divididos, uma query sobre "como abrir chamado de devolução" pode recuperar apenas o passo 1 ou 2 sem os demais, gerando orientação incompleta.

### 3.3. Problema do "Lost in the Middle" — Estratégia de Mitigação Específica

**Padrão de query esperado:** "Posso devolver [tipo de carga]?" / "Qual o prazo para devolver?"

**Risco:** Usuário pergunta sobre devolução, sistema recupera POL-001-A (prazo) mas não POL-001-B (exceções). Resposta incompleta: "sim, pode em 7 dias" sem mencionar que carga perigosa é exceção.

**Mitigação recomendada:**

1. **Chunk colocado junto (pair chunking):** Criar um chunk composto POL-001-AB que une seções 3.1 + 3.2, pois estas são semanticamente interdependentes.

```
Chunk POL-001-AB (composto):
"Prazo geral: 7 dias úteis. EXCEÇÕES — NÃO elegíveis pelo processo padrão:
cargas perigosas classes 1-6 ANTT, cargas refrigeradas com ruptura de cadeia fria,
cargas com lacre violado. Para esses casos: Gestão de Riscos ramal 4500."
Tokens: ~250
```

2. **Posicionamento no contexto:** Colocar chunks de exceções (POL-001-B) sempre no **início** do contexto montado, não no meio.

3. **Instrução no system prompt:** "Ao responder sobre devolução, sempre verifique se há exceções aplicáveis ao tipo de carga mencionado."

### 3.4. Considerações sobre Desafios Técnicos Mencionados no Projeto

Este documento é fornecido como Markdown limpo. Entretanto, na base real da NovaTech (800 PDFs, 400 páginas wiki), documentos similares podem conter:

| Desafio técnico      | Impacto                              | Solução                                        |
|----------------------|--------------------------------------|------------------------------------------------|
| PDFs escaneados (OCR)| Texto extraído com erros de caractere| Azure Document Intelligence (OCR + layout) antes do chunking |
| Fluxogramas em imagens| Procedimentos visuais não capturados | Extração multi-modal (GPT-4V para descrever fluxograma em texto) |
| Tabelas complexas    | Perda de estrutura linhas×colunas    | Table extraction separada; chunk de tabela serializada como texto |
| Versões concorrentes | Chunks v1 e v2 no mesmo índice       | Metadado `version_status: active/deprecated` + filtro de busca |

### 3.5. Riscos específicos deste documento no pipeline RAG

| Risco                          | Descrição                                                             | Mitigação                                        |
|-------------------------------|-----------------------------------------------------------------------|--------------------------------------------------|
| Resposta incompleta sobre exceções | POL-001-A recuperado sem POL-001-B = resposta juridicamente errada  | Pair chunking 3.1+3.2 ou instrução de recuperação obrigatória |
| Confusão com carga em trânsito | Documento só cobre pós-entrega (escopo seção 2)                      | Metadado de escopo no chunk + referência a PROC-088 |
| FAQ-03 contradizendo POL-001-B | FAQ diz "pode ser exceção", POL diz "não pelo processo padrão"       | Filtro de autoridade: POL > FAQ para queries de elegibilidade |
| Devolução parcial subestimada  | Seção 3.4 raramente recuperada se query não mencionar "parcial"       | Sinônimos na query expansion: "volume específico", "item único" |

---

## Resumo Executivo

A POL-001 é o documento de **maior autoridade** para queries de devolução — versão formal, normativa e recente (jan/2024). Com ~693 tokens, gera 5 chunks focados que cobrem prazo, exceções, procedimento, devolução parcial e custos. O maior risco RAG é a **recuperação incompleta da regra de exceções** (seção 3.2): um pipeline que retorna prazo sem exceções gera respostas juridicamente problemáticas. A solução é pair chunking das seções 3.1+3.2 e posicionamento preferencial no início do contexto. Este documento deve ter **prioridade de ranqueamento sobre o FAQ-atendimento** em todas as queries relacionadas a devolução.

---

## Feedback Técnico — Revisão Crítica da Análise

> **Revisão por:** Engenheiro de IA (RAG)  
> **Data:** 2026-05-28  
> **Escopo:** Identificação de estimativas otimistas, pontos fracos e riscos não considerados na primeira versão desta análise.

---

### F.1. Estimativas Otimistas Demais

#### F.1.1. Tokens por seção subestimam overhead de metadados no chunk
Os tokens estimados por seção (ex.: Seção 3.2 com ~173 tokens) refletem apenas o **conteúdo bruto do documento Markdown**. Quando aplicado o template de chunk recomendado (com cabeçalho de fonte, versão, data, tipo, referências cruzadas), cada chunk ganha ~40–60 tokens de overhead de metadados. O chunk POL-001-B estimado em ~180 tokens cresce para ~230–240 tokens. Para o corpus inteiro, isso representa ~20–25% de inflação nos tokens reais armazenados no índice — relevante para estimar custo de embedding e armazenamento vetorial.

#### F.1.2. Pair chunking POL-001-AB com ~250 tokens ignora duplicação no índice
A análise recomenda criar um chunk composto POL-001-AB (3.1 + 3.2) de ~250 tokens *além* dos chunks individuais POL-001-A e POL-001-B. Isso cria **conteúdo duplicado no índice**: a seção 3.2 aparece em dois chunks distintos (o individual POL-001-B e o composto AB). Em retrieval por similaridade, ambos podem ser recuperados para a mesma query, consumindo tokens redundantes no contexto. A análise não discute a estratégia de **deduplicação pós-retrieval** nem sugere indexar apenas o composto e eliminar os individuais, o que seria mais limpo.

#### F.1.3. Corpus: estimativa de planilhas (1.000 pal/planilha) é a mais frágil
Idêntico ao problema identificado no FAQ: 50 planilhas a 1.000 palavras equivalentes é provavelmente 5–15× subestimado para tabelas de frete operacional. Este gap afeta todas as 5 análises pois usam o mesmo número de corpus.

---

### F.2. Pontos Fracos da Análise

#### F.2.1. Estratégia de posicionamento de chunks requer orquestração customizada
A análise recomenda posicionar POL-001-B (exceções) **sempre no início** do contexto e FAQ no final. Essa reordenação exige que o pipeline aplique **lógica de ordenação pós-retrieval** antes de montar o prompt — uma camada de orquestração que o Azure AI Search não fornece nativamente. A complexidade de implementar e manter essa lógica (especialmente quando múltiplos documentos de tipos diferentes são recuperados) é **subestimada**: quem define a prioridade quando há 3 documentos de alta autoridade? Como isso é testado em regressão?

#### F.2.2. PROC-088 referenciado mas inexistente na base
A seção 2 da POL-001 menciona `PROC-088: Procedimento de Interceptação de Carga` para cargas em trânsito. Este documento **não está na base de análise** e não é mencionado como gap. Queries como "minha carga está em trânsito, como cancelo a entrega?" seriam respondidas com base na POL-001 (que apenas redireciona para PROC-088) sem que o assistente tenha o procedimento real. A análise menciona a referência cruzada como metadado, mas não levanta o risco de **gap de cobertura para um tópico operacional relevante** (interceptação de carga em trânsito é provavelmente uma pergunta frequente).

#### F.2.3. Seção 3.4 (Devoluções Parciais) subrepresentada nos casos de uso
A análise categoriza POL-001-D (Devoluções Parciais) como "Independente" e não discute os padrões de query que a ativariam. Perguntas como "posso devolver só 3 volumes dos 10 entregues?" ou "recebi metade da carga danificada" são casos de uso reais que requerem esse chunk — mas a análise não inclui esses padrões de query nos exemplos, criando risco de que o chunk seja subotimizado para retrieval (sem keywords de "volumes", "parcial", "múltiplos itens" no template).

#### F.2.4. Ausência de discussão sobre versionamento futuro
A POL-001 está na v3.1 e tem "Última atualização: 15/01/2024". Políticas normativas são revisadas periodicamente. A análise não discute **o que acontece quando a v3.2 for publicada**: como o pipeline detecta a nova versão? Como os chunks da v3.1 são invalidados? Como garantir que não haja coexistência de chunks v3.1 e v3.2 no índice (o mesmo problema da PROC-042, mas para um documento de alta autoridade jurídica)?

---

### F.3. Riscos Não Considerados

#### F.3.1. Ausência de política formal para carga danificada cria risco jurídico latente
O Anexo A identifica que não existe documento formal (POL ou PROC) para carga danificada em trânsito — apenas o FAQ-38 informal. A POL-001, como política mais abrangente de devolução, **limita seu escopo explicitamente à pós-entrega** (seção 2). Quando um atendente pergunta "o que fazer com carga danificada?", o sistema pode recuperar POL-001-C (procedimento de devolução pós-entrega) e aplicá-lo erroneamente a um caso de dano em trânsito — situação juridicamente diferente. A análise não levanta esse risco de **aplicação de política no escopo errado**.

#### F.3.2. Regra de 4h úteis para triagem (seção 3.3) conflita com SLA de resposta
A seção 3.3 estabelece que o time de atendimento tem **4 horas úteis para triagem** de um chamado de devolução. O SLA-2024 define que clientes Gold têm SLA de **2 horas úteis** para primeira resposta em chamados gerais. Para um cliente Gold que abre chamado de devolução, os dois documentos criam uma tensão: a POL-001 permite 4h para triagem, mas o SLA garante ao Gold resposta em 2h. A análise não identifica esta **contradição interna entre documentos** que o LLM precisaria resolver corretamente.

#### F.3.3. "Prazo expirado" (seção 3.5) não cobre todos os casos de borda
A seção 3.5 redireciona solicitações após 7 dias úteis ao Comercial "para negociação caso a caso". Mas e se o cliente perdeu o prazo por falha no Portal do Cliente (indisponibilidade do sistema de tracking)? Esse caso de borda não está na POL-001, mas é operacionalmente provável em uma transportadora. O LLM que responder com base apenas na POL-001 pode negar a devolução a um cliente com direito a ela por motivo de força maior — **risco de prejudicar o cliente por omissão documental**.

#### F.3.4. Ausência de teste de recuperação para queries negativas
A análise discute retrieval para queries afirmativas ("posso devolver?", "qual o prazo?"), mas não para queries negativas que deveriam retornar POL-001-B como resposta primária: "minha carga tem lacre violado, posso devolver normalmente?", "carga refrigerada que perdeu temperatura — tem devolução?". Essas queries são semanticamente distantes da frase "7 dias úteis" (seção 3.1) que domina o espaço de embedding de "devolução". O recall de POL-001-B para essas queries específicas **precisa ser testado empiricamente** — a análise assume que será recuperado, mas não valida essa premissa.
