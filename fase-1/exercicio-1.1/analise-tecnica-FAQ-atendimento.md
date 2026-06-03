# Análise Técnica RAG — FAQ-atendimento.md

**Fonte analisada:** FAQ-Atendimento — Perguntas Frequentes do Time de Suporte  
**Data da análise:** 2026-05-28  
**Contexto do projeto:** Pipeline RAG para assistente de atendimento NovaTech (GPT-4o, Azure AI Search)

---

## 1. Estimativa de Tamanho em Tokens

### 1.1. Tamanho do documento individual

| Componente                  | Palavras (est.) | Tokens (÷ 0,75) |
|-----------------------------|-----------------|-----------------|
| Cabeçalho + metadados       | ~50             | ~67             |
| Aviso interno               | ~60             | ~80             |
| 9 itens de FAQ (perguntas + respostas) | ~460  | ~613            |
| **Total do documento**      | **~570**        | **~760**        |

> Regra aplicada: 1 token ≈ 0,75 palavras (padrão OpenAI/tiktoken para português)

### 1.2. Estimativa do corpus completo (base NovaTech)

| Tipo de documento           | Volume       | Palavras médias  | Total palavras  | Total tokens    |
|-----------------------------|--------------|------------------|-----------------|-----------------|
| PDFs                        | 800 docs     | 10 pág × 300 pal | 2.400.000       | 3.200.000       |
| Páginas wiki                | 400 páginas  | 1.500 pal/página | 600.000         | 800.000         |
| Planilhas                   | 50 arquivos  | ~1.000 pal equiv.| 50.000          | 66.667          |
| **Total estimado**          |              |                  | **3.050.000**   | **~4.067.000**  |

> O corpus completo tem aproximadamente **4 milhões de tokens** — cerca de 31× o tamanho da janela do GPT-4o (128k).

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

**Isso representa ~6,1% do corpus total** (249 de ~4.067 chunks equivalentes).

### 2.3. Por que NÃO usar os 249 chunks disponíveis — efeito "Lost in the Middle"

Pesquisa empírica (Liu et al., 2023) demonstra que LLMs têm atenção não uniforme ao longo do contexto:

```
Posição no contexto:  [INÍCIO]  [MEIO]  [FIM]
Taxa de recall:        ~95%      ~60%    ~88%
```

Com 249 chunks (~124k tokens), aproximadamente **~200 chunks ficariam na zona intermediária** com recall degradado. O modelo responderia bem à pergunta usando apenas os chunks no início e fim, desperdiçando 80% do contexto injetado e aumentando o risco de contradições.

### 2.4. Recomendação de Top-K para este documento

| Estratégia       | Chunks recuperados | Tokens usados | % do disponível | Qualidade esperada |
|------------------|-------------------|---------------|-----------------|-------------------|
| Mínimo           | 3                 | ~1.500        | 1,2%            | Alta (sem perda)  |
| Recomendado      | 5–8               | ~2.500–4.000  | 2–3,2%          | Alta (sem perda)  |
| Limite prático   | 15                | ~7.500        | 6%              | Boa (risco baixo) |
| Evitar           | >20               | >10.000       | >8%             | Degradação        |

> Para queries típicas de atendimento ao cliente (perguntas curtas e diretas), **Top-K = 5** é suficiente e garante que todos os chunks fiquem próximos ao início do contexto.

---

## 3. Recomendações de Estratégia de Chunking

### 3.1. Características do documento que impactam o chunking

| Característica              | Impacto no RAG                                              |
|-----------------------------|-------------------------------------------------------------|
| Documento informal, não versionado | Sem garantia de atualidade — metadado de confiabilidade obrigatório |
| 47 itens (apenas 9 mostrados) | Cada item é semanticamente independente — favorece chunking item-a-item |
| Linguagem coloquial          | Embeddings de perguntas formais podem não recuperar bem       |
| Contradições com docs formais| Alto risco: FAQ pode ser recuperado em vez de POL/PROC         |
| Sem responsável formal       | Metadado de autoridade = baixo                              |

### 3.2. Estratégia recomendada: Chunking por Item FAQ com Metadados de Confiabilidade

**Unidade de chunk:** 1 chunk = 1 item FAQ (pergunta + resposta)

**Template de chunk:**
```
[FONTE: FAQ-Atendimento | TIPO: Documento informal | CONFIABILIDADE: Baixa]
[Tópico: {categoria inferida}]

Pergunta: {pergunta do item}
Resposta prática: {resposta do atendente}

⚠️ Esta informação não foi validada contra documentos normativos (POL/PROC/SLA).
Confirmar com documentação oficial antes de usar em contextos críticos.
```

**Justificativa:** A pergunta do usuário tende a ser semanticamente próxima da "Pergunta:" do FAQ, maximizando recall por similaridade. O contexto de confiabilidade impede que o LLM trate informação informal como autoridade.

### 3.3. Chunks gerados por este documento

| Chunk ID     | Conteúdo                                      | Tokens (est.) | Risco de contradição |
|--------------|-----------------------------------------------|---------------|----------------------|
| FAQ-03       | Devolução de carga perigosa                   | ~80           | Alto (vs POL-001)    |
| FAQ-08       | Como funciona o frete especial                | ~90           | Alto (v1 vs v2)      |
| FAQ-15       | Tier Platinum inexistente                     | ~70           | Baixo (confirma SLA) |
| FAQ-22       | Seguro de carga (percentuais)                 | ~80           | Médio (sem doc formal) |
| FAQ-27       | Tracking parado há 5 dias                     | ~75           | Baixo                |
| FAQ-32       | Carga perigosa com frete expresso             | ~70           | Alto (sem doc formal)|
| FAQ-38       | Carga danificada em trânsito                  | ~85           | Alto (sem doc formal)|
| FAQ-41       | Diferença SLA resposta vs resolução           | ~80           | Baixo (confirma SLA) |
| FAQ-45       | Desconto no frete                             | ~70           | Médio (v1 vs v2)     |

### 3.4. Considerações sobre o efeito "Lost in the Middle" neste documento

Perguntas de atendimento são **curtas e diretas** ("qual o prazo de devolução?", "o que é SLA Gold?"). Isso favorece retrieval de **chunks pequenos e focados** (como os deste FAQ). O risco de "lost in the middle" é controlado mantendo Top-K baixo (≤8) e garantindo que chunks contraditórios de fontes formais sejam priorizados.

**Estratégia de posicionamento:** Ao montar o prompt, posicionar chunks do FAQ ao **final** do contexto (menor perda de atenção) e chunks normativos (POL/PROC) ao **início**.

### 3.5. Riscos específicos deste documento no pipeline RAG

| Risco                          | Descrição                                                        | Mitigação recomendada                              |
|-------------------------------|------------------------------------------------------------------|----------------------------------------------------|
| FAQ sobrepondo POL formal      | FAQ-03 contradiz POL-001-B (exceção informal vs regra formal)   | Filtro de fonte: priorizar POL sobre FAQ em topics de devolução |
| Informação sem respaldo formal | FAQ-32 e FAQ-38 não têm PROC correspondente                      | Adicionar nota de incerteza no sistema prompt      |
| Versão desatualizada           | Alerta sobre duas PROC-042 pode confundir se FAQ for recuperado  | Metadado de data de atualização no chunk           |
| Linguagem informal             | Embeddings podem não alinhar com queries formais                 | Considerar query expansion ou HyDE (HypotheticalDocument Embeddings) |

---

## Resumo Executivo

O FAQ-atendimento.md é um documento de **baixa autoridade e alta relevância prática**. Com ~760 tokens de conteúdo, gera 9 chunks altamente focados (70–90 tokens cada), ideais para retrieval semântico de queries curtas. O principal risco RAG é a **contradição com documentos normativos**: o pipeline deve implementar ranqueamento por autoridade da fonte, não apenas por similaridade semântica. Nunca deve ser a única fonte para decisões críticas (devolução de carga perigosa, cálculo de frete em disputas contratuais).

---

## Feedback Técnico — Revisão Crítica da Análise

> **Revisão por:** Engenheiro de IA (RAG)  
> **Data:** 2026-05-28  
> **Escopo:** Identificação de estimativas otimistas, pontos fracos e riscos não considerados na primeira versão desta análise.

---

### F.1. Estimativas de Corpus Otimistas Demais

#### F.1.1. Densidade de palavras por página de PDF (300 pal/página)
A estimativa de 300 palavras/página usada no cálculo do corpus é **o limite inferior do intervalo realista** para PDFs operacionais. PDFs de políticas, procedimentos e manuais técnicos com parágrafos densos facilmente têm 400–500 palavras/página. Usando 400 palavras/página, o corpus saltaria de ~3,2M para ~4,3M tokens só nos PDFs — um aumento de ~34%. A estimativa atual pode criar falsa sensação de conforto sobre o tamanho do problema de retrieval.

**Contrapartida real:** PDFs com tabelas pesadas, cabeçalhos/rodapés repetidos, figuras e muito espaço em branco podem ter menos de 300 palavras/página de conteúdo útil. O risco existe nas duas direções, e a análise trata como fato um único ponto da faixa.

#### F.1.2. Planilhas a ~1.000 palavras equivalentes cada
Esta é a estimativa **mais otimista e provavelmente mais errada** do corpus inteiro. Uma única tabela mensal de fretes (`frete-base-AAAAMM.xlsx`) com rotas entre municípios, pesos, classes de frete e valores pode ter centenas de linhas × dezenas de colunas. Serializada para ingestão no pipeline, isso pode representar 5.000–20.000 "palavras equivalentes" por planilha, não 1.000. Com 50 planilhas dessa natureza, o componente de planilhas poderia ser 10–20× maior que o estimado (500.000–1.000.000 tokens em vez de ~67.000). Isso eleva o corpus total estimado para **5–7 milhões de tokens**, não 4 milhões.

#### F.1.3. Relação palavras/token para português (0,75)
A regra de 0,75 palavras/token (equivalente a ~1,33 tokens/palavra) é derivada predominantemente de corpus em **inglês**. Português brasileiro tem morfologia mais rica (artigos, preposições contraídas, terminações verbais, gênero/número), o que infla o número de tokens por palavra. Estudos com tiktoken (cl100k_base) em português mostram relações de **0,65–0,70 palavras/token** (~1,43–1,54 tokens/palavra). Usando 0,68 como estimativa, o corpus sobe de ~4,07M para ~4,5M tokens — diferença de ~10% que pode ser relevante em projetos onde o custo de embedding é faturado por token.

---

### F.2. Pontos Fracos da Análise

#### F.2.1. Chunks muito pequenos (70–90 tokens) sem discussão de contexto envolvente
Chunks de 70–90 tokens equivalem a ~50–65 palavras — menos de 4 frases. Em muitos casos, esses chunks **perdem contexto suficiente para serem autoexplicativos**. O item FAQ-03 ("Devolução de carga perigosa") com ~80 tokens responde a uma pergunta específica, mas o LLM pode precisar de contexto para entender que está tratando de uma *exceção ao processo padrão*, não de uma política separada. A análise recomenda chunking item-a-item, mas não discute estratégias de **parent document retrieval** (recuperar o chunk pequeno pela similaridade, mas enviar ao LLM o chunk maior que o contém) ou **sliding window com overlap**, que mitigariam a perda de contexto.

#### F.2.2. Ausência de discussão sobre o modelo de embedding
A análise pressupõe que a busca semântica funcionará bem com o texto do FAQ, mas **não especifica qual modelo de embedding usar**. Esta é uma decisão crítica para português. O `text-embedding-ada-002` (inglês-centric) pode ter qualidade inferior ao `text-embedding-3-large` ou modelos multilíngues como `multilingual-e5-large` para textos com terminologia logística em português. A diferença de recall@5 entre modelos pode ser de 15–30% dependendo do domínio — silenciar isso é um risco técnico relevante.

#### F.2.3. Sem menção a busca híbrida (vetor + BM25)
O Azure AI Search suporta **hybrid retrieval** (vetor + keyword BM25). Para queries que contenham termos exatos como "FAQ-03", "ramal 4500", "CT-e", ou nomes de procedimentos, a busca por palavras-chave frequentemente supera a busca vetorial. A análise foca exclusivamente em retrieval por similaridade semântica, omitindo uma funcionalidade nativa da plataforma que reduziria significativamente falhas de retrieval para queries com termos técnicos específicos.

#### F.2.4. Sem proposta de metodologia de avaliação
A análise identifica riscos e recomenda estratégias, mas não propõe **como medir se o pipeline funciona corretamente** para este documento. Um projeto RAG sem conjunto de avaliação (pares pergunta → chunks esperados → resposta esperada) opera às cegas. O Anexo B já fornece um `Mapa de cobertura: pergunta → chunks recuperados` que poderia ser usado como ponto de partida para um evaluation set — essa oportunidade não foi explorada.

---

### F.3. Riscos Não Considerados

#### F.3.1. Ausência do restante dos 47 itens do FAQ
A análise só cobre 9 dos 47 itens do FAQ original. Os **38 itens ausentes** podem conter informações contraditórias com documentos formais, informações sobre tópicos sem documento formal (como os gaps identificados no Anexo A), ou confirmações de políticas. Sem analisar os 38 itens restantes, a análise de riscos de contradição é necessariamente incompleta — pode haver contradições mais graves ocultas no FAQ completo.

#### F.3.2. Risco de re-indexação não tratado
O FAQ é descrito como "documento colaborativo" sem responsável formal, atualizado organicamente pelo time. Isso implica que **o conteúdo muda com frequência desconhecida**. O pipeline precisa de um mecanismo de detecção de mudança (hash de conteúdo, webhook no SharePoint, polling) e re-indexação incremental. A análise não discute o risco de o índice vetorial ficar desatualizado em relação ao FAQ em produção.

#### F.3.3. Risco de o FAQ ser a única fonte para tópicos sem documento formal
FAQ-32 (carga perigosa com frete expresso) e FAQ-38 (carga danificada) não têm PROC correspondente. A análise recomenda "adicionar nota de incerteza no system prompt", mas isso é insuficiente: se esses tópicos aparecerem em queries críticas e o FAQ for o único chunk recuperado, o LLM será forçado a ou usar informação não validada ou dizer "não sei" — ambos problemáticos. O risco real é que **a inexistência de documentação formal para esses tópicos é um gap de governança documental**, não apenas um problema de RAG, e deveria ser escalado ao responsável de Compliance/Operações como pré-requisito para a produção do pipeline.

#### F.3.4. Ausência de re-ranker no pipeline
A análise discute retrieval (Top-K) mas não menciona a etapa de **re-ranking** pós-retrieval. Em um corpus com documentos de autoridade diferente (POL formal vs. FAQ informal) cobrindo os mesmos tópicos, um cross-encoder re-ranker (como Cohere Rerank ou um modelo fine-tuned) é a camada mais eficaz para garantir que documentos de alta autoridade fiquem no topo — antes mesmo de qualquer lógica de posicionamento manual no contexto. Sem re-ranker, a estratégia de "posicionar FAQ no final do contexto" exige orquestração manual frágil.

#### F.3.5. System prompt e buffer de resposta subestimados
A análise aloca ~2.000 tokens para system prompt e ~1.000 tokens para buffer de resposta. Para um assistente de atendimento de transportadora, um system prompt robusto tipicamente inclui: definição de papel, hierarquia de fontes, regras de escalação, instruções de formato, disclaimers legais e exemplos few-shot. Isso facilmente consome **3.500–6.000 tokens**. A resposta gerada para uma pergunta multi-passo (procedimento de devolução, por exemplo) pode ter 800–2.500 tokens. O "disponível para chunks" real pode ser **4.000–8.000 tokens menor** que os 124.800 estimados — reduzindo o Top-K máximo sem degradação de ~249 para ~230–240 chunks, o que não muda drasticamente as recomendações, mas o orçamento real precisa ser aferido com o prompt de produção, não com a estimativa teórica.
