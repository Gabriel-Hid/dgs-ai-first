# Análise Técnica RAG — SLA-2024-tabela-sla-clientes.md

**Fonte analisada:** SLA-2024 — Tabela de SLA por Tipo de Cliente (v2024.1, 02/01/2024)  
**Data da análise:** 2026-05-28  
**Contexto do projeto:** Pipeline RAG para assistente de atendimento NovaTech (GPT-4o, Azure AI Search)

---

## 1. Estimativa de Tamanho em Tokens

### 1.1. Tamanho do documento individual

| Seção                                         | Palavras (est.) | Tokens (÷ 0,75) |
|-----------------------------------------------|-----------------|-----------------|
| Cabeçalho + metadados                         | ~35             | ~47             |
| Seção 1 — Classificação de clientes (tabela)  | ~80             | ~107            |
| Seção 2 — Tabela de SLAs (7 métricas × 3 tiers) | ~120         | ~160            |
| Seção 3 — Definição de incidente crítico      | ~80             | ~107            |
| Seção 4 — Penalidades por descumprimento      | ~70             | ~93             |
| Seção 5 — Medição e reportes                  | ~65             | ~87             |
| **Total do documento**                        | **~450**        | **~600**        |

> Regra aplicada: 1 token ≈ 0,75 palavras (padrão OpenAI/tiktoken para português)  
> Tabelas Markdown têm overhead de ~20% por pipes e espaços de alinhamento

### 1.2. Estimativa do corpus completo (base NovaTech)

| Tipo de documento           | Volume       | Palavras médias  | Total palavras  | Total tokens    |
|-----------------------------|--------------|------------------|-----------------|-----------------|
| PDFs                        | 800 docs     | 10 pág × 300 pal | 2.400.000       | 3.200.000       |
| Páginas wiki                | 400 páginas  | 1.500 pal/página | 600.000         | 800.000         |
| Planilhas                   | 50 arquivos  | ~1.000 pal equiv.| 50.000          | 66.667          |
| **Total estimado**          |              |                  | **3.050.000**   | **~4.067.000**  |

> O corpus completo tem ~4 milhões de tokens — ~31× a janela GPT-4o. A SLA-2024 representa ~0,015% do corpus total, mas é chamada em alto percentual das queries de atendimento.

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

### 2.3. Análise de ocupação de contexto para queries de SLA

A SLA-2024 é chamada em **dois cenários muito diferentes** de query, com impactos distintos no orçamento:

**Cenário A — Query simples sobre um tier:**
```
Query: "Qual o SLA do cliente Gold?"
Chunks necessários: SLA-2024-B (2 chunks: chamados gerais + incidentes críticos)
Tokens usados: ~200 tokens  ← 0,16% da janela disponível
```

**Cenário B — Query sobre classificação de tier:**
```
Query: "Meu cliente é Platinum, qual o SLA dele?"
Chunks necessários: SLA-2024-A (classificação)
Tokens usados: ~120 tokens  ← 0,10% da janela disponível
Resultado esperado: LLM informa que Platinum não existe
```

**Cenário C — Query multi-dimensão (SLA + incidente + penalidade):**
```
Query: "É um cliente Silver, com carga de R$150k parada há 8h, o que acontece?"
Chunks necessários: SLA-2024-A + SLA-2024-C + SLA-2024-D + SLA-2024-E
Tokens usados: ~500 tokens  ← 0,40% da janela disponível
```

Em todos os cenários, **o orçamento de contexto para SLA-2024 é confortavelmente pequeno**. O risco de "lost in the middle" para este documento específico é baixo desde que o Top-K seja mantido em ≤15 chunks totais.

### 2.4. Análise do efeito "Lost in the Middle" para a tabela de SLA

A tabela de SLA (seção 2) é uma **matriz 7×3** (7 métricas × 3 tiers). Se serializada como texto plano, cada linha da tabela ocupa ~30-40 tokens. O LLM precisa correlacionar linha (métrica) com coluna (tier) — isso é vulnerável ao "lost in the middle":

```
Contexto com tabela serializada como texto longo:
[INÍCIO] "Gold: resposta 2h, resolução 24h"         (alta atenção)
[MEIO]   "Silver: resposta 4h, resolução 48h"       (atenção media)
[MEIO]   "Standard: resposta 8h, resolução 72h"     (atenção media)
[MEIO]   "Gold crítico: resposta 30min, resol. 4h"  (atenção baixa) ← CRÍTICO
[MEIO]   "Silver crítico: resposta 1h, resol. 8h"   (atenção baixa)
[FIM]    "penalidades..."                            (alta atenção)

→ LLM pode confundir SLA de "chamados gerais" com "incidentes críticos"
→ Risco: informar Gold tem resposta 2h para incidente crítico (correto: 30min)
```

**Mitigação:** Serializar a tabela com contexto explícito de dimensão em cada linha, ou dividir em dois chunks (chamados gerais vs. incidentes críticos).

### 2.5. Recomendação de Top-K para queries de SLA

| Tipo de query                      | Chunks necessários | Tokens | Top-K recomendado |
|------------------------------------|--------------------|--------|-------------------|
| SLA de um tier específico          | 2–3                | ~300   | 3–5               |
| Verificação de tier inexistente    | 1                  | ~120   | 3                 |
| Incidente crítico + penalidades    | 3–4                | ~450   | 5–8               |
| Query completa (todos aspectos)    | 5                  | ~600   | 8                 |

---

## 3. Recomendações de Estratégia de Chunking

### 3.1. Características do documento que impactam o chunking

| Característica                      | Impacto no RAG                                                       |
|-------------------------------------|----------------------------------------------------------------------|
| Documento contratual (SLAs formais) | Autoridade máxima — informação tem implicação jurídica               |
| Tabela 7×3 (métricas × tiers)       | Estrutura matricial complexa — serialização inadequada perde relações|
| Dois tipos de SLA (geral vs crítico)| Confundíveis semanticamente — separar em chunks distintos            |
| Definição de incidente crítico       | 4 critérios OR — qualquer um ativa SLA crítico                       |
| Penalidades por violação             | 3 níveis progressivos — manter como unidade                          |
| Nota: Platinum não existe            | Query trap (tier inexistente) — chunk deve ser explicitamente negativo|
| SLA não pausa para Gold crítico      | Regra especial crítica — fácil de perder em serialização de tabela   |

### 3.2. Estratégia recomendada: Chunking Funcional por Tipo de Consulta

Em vez de chunking por seção estrutural (1, 2, 3, 4, 5), recomendar chunking **orientado ao padrão de pergunta** do atendente:

**Template de chunk:**
```
[FONTE: SLA-2024 | VERSÃO: 2024.1 | DATA: 02/01/2024 | TIPO: Documento contratual | AUTORIDADE: Máxima]
[Tópico: {classificação / sla-geral / sla-critico / incidente-critico / penalidades / medicao}]

{conteúdo serializado}
```

### 3.3. Chunking recomendado

| Chunk ID      | Conteúdo                                                     | Tokens (est.) | Casos de uso                         |
|---------------|--------------------------------------------------------------|---------------|--------------------------------------|
| SLA-2024-A    | Classificação de tiers (Gold/Silver/Standard + critérios) + nota sobre Platinum inexistente | ~120 | "Sou Platinum?", "Qual é meu tier?" |
| SLA-2024-B    | SLAs chamados gerais (resposta + resolução por tier)         | ~130          | "Qual SLA do Gold?", "Prazo de resposta Silver?" |
| SLA-2024-C    | SLAs incidentes críticos (por tier) + nota Gold não pausa    | ~120          | "É incidente crítico, qual SLA?" |
| SLA-2024-D    | Definição de incidente crítico (4 critérios)                 | ~110          | "Isso é incidente crítico?", "Carga R$150k parada" |
| SLA-2024-E    | Penalidades por violação (3 níveis progressivos)             | ~100          | "O prazo foi violado, o que acontece?" |

> **Total: 5 chunks, ~580 tokens** — o documento completo cabe confortavelmente em ~1 chunk de contexto, mas é melhor dividir para precisão de retrieval.

### 3.4. Serialização recomendada da tabela de SLA (seção 2)

**Evitar:** Reproduzir a tabela Markdown diretamente (dificulta correlação linha×coluna em contextos longos)

**Preferir:** Serialização orientada por tier dentro de cada chunk:

```
Chunk SLA-2024-B — SLAs para chamados gerais:
  GOLD:     1ª resposta → até 2h úteis | Resolução → até 24h úteis
  SILVER:   1ª resposta → até 4h úteis | Resolução → até 48h úteis
  STANDARD: 1ª resposta → até 8h úteis | Resolução → até 72h úteis
  Horário comercial: 08h-18h dias úteis (relógio pausa fora desse horário para chamados gerais)
```

```
Chunk SLA-2024-C — SLAs para incidentes críticos:
  GOLD:     1ª resposta → até 30min | Resolução → até 4h
            ⚠️ GOLD: relógio NÃO pausa fora do horário comercial para incidentes críticos
  SILVER:   1ª resposta → até 1h    | Resolução → até 8h
  STANDARD: 1ª resposta → até 2h    | Resolução → até 24h
```

> Serializar a exceção "relógio não pausa para Gold crítico" **dentro do chunk SLA-2024-C** garante que ela seja recuperada exatamente quando necessária.

### 3.5. O chunk SLA-2024-A como "negação ativa" para tier inexistente

O FAQ-15 menciona que clientes frequentemente perguntam sobre "tier Platinum". O chunk SLA-2024-A deve ser construído para responder **diretamente** a essa query:

```
Chunk SLA-2024-A — Classificação de tiers:
  A NovaTech classifica clientes em 3 tiers:
  - GOLD: contrato anual > R$500.000 OU >200 operações/mês (revisão semestral)
  - SILVER: contrato entre R$100.000–R$500.000 OU 50-200 operações/mês (revisão semestral)
  - STANDARD: todos os demais clientes (revisão anual)
  
  ❌ NÃO EXISTEM outros tiers (Platinum, Bronze, Diamond, etc.).
  Para SLA diferenciado fora desses tiers: encaminhar ao Comercial.
```

A frase "NÃO EXISTEM outros tiers" em negrito/explícita aumenta a probabilidade de o LLM recuperar e usar corretamente este trecho quando o cliente citar um tier inexistente.

### 3.6. Riscos específicos deste documento no pipeline RAG

| Risco                          | Descrição                                                               | Mitigação                                           |
|-------------------------------|-------------------------------------------------------------------------|-----------------------------------------------------|
| Confusão SLA geral vs crítico  | LLM informa 2h para Gold em vez de 30min para incidente crítico         | Chunks separados por tipo de SLA + distinção explícita |
| Tier Platinum inventado        | LLM alucina SLAs para tier inexistente se SLA-2024-A não for recuperado | Negação explícita no chunk + query expansion para "Platinum" |
| Relógio pausa mal aplicado     | LLM esquece que Gold crítico não pausa → cálculo de SLA errado          | Nota de exceção embutida no chunk SLA-2024-C        |
| Disponibilidade do portal omitida | SLA de disponibilidade 99,5%/99%/98% raramente recuperado sem query específica | Chunk SLA-2024-B pode incluir linha de disponibilidade |
| Penalidade primeira violação trivializada | "Sem impacto contratual" pode ser omitido → cliente não entende progressividade | Chunk SLA-2024-E deve manter os 3 níveis juntos |

### 3.7. Considerações sobre Desafios Técnicos do Projeto

| Desafio técnico      | Relevância para SLA-2024                              | Solução                                         |
|----------------------|-------------------------------------------------------|-------------------------------------------------|
| PDFs escaneados (OCR)| Tabelas de SLA em PDF podem ter colunas trocadas após OCR | Validação estrutural pós-extração              |
| Tabelas complexas    | Matriz 7×3 — extração direta de PDF perde alinhamento | Table extraction dedicada (Azure Document Intelligence) |
| Fluxogramas          | Fluxo de escalação pode estar em imagem              | Extração multi-modal para descrever fluxograma  |
| Planilhas            | Relatórios de performance (SLA medido) podem estar em xlsx | Ingestão separada com link cruzado para SLA-2024 |

---

## Resumo Executivo

A SLA-2024 é o documento de **maior autoridade contratual** da base — seus valores têm implicação jurídica direta. Com ~600 tokens, gera 5 chunks altamente especializados por tipo de consulta. Os principais riscos RAG são: (1) confusão entre SLA de chamados gerais e incidentes críticos ao serializar a tabela 7×3 sem separação de dimensão; (2) alucinação de tier Platinum quando SLA-2024-A não é recuperado. A estratégia de chunking funcional (por padrão de pergunta) supera o chunking estrutural (por seção do documento) para este caso. A serialização orientada por tier — em vez de tabela Markdown — é recomendada para garantir correlação correta entre métrica, tier e valor de SLA no contexto do LLM.

---

## Feedback Técnico — Revisão Crítica da Análise

> **Revisão por:** Engenheiro de IA (RAG)  
> **Data:** 2026-05-28  
> **Escopo:** Identificação de estimativas otimistas, pontos fracos e riscos não considerados na primeira versão desta análise.

---

### F.1. Estimativas Otimistas Demais

#### F.1.1. "Orçamento confortavelmente pequeno" para SLA — conclusão válida mas com ressalva
A análise conclui que o orçamento de contexto para SLA-2024 é "confortavelmente pequeno" (até ~600 tokens em todos os cenários). Isso é verdade para queries **sobre SLA em isolamento**. Mas queries de atendimento real são frequentemente **multi-domínio**: "cliente Silver com carga perigosa acima de 5.000 kg parada há 8 horas, qual o SLA e qual o frete de devolução?" Nesse caso, o sistema precisaria de chunks de SLA-2024 + POL-001 + PROC-042-v2 + possivelmente FAQ, consumindo 1.200–2.000 tokens de chunks só para esse conjunto. O cenário multi-domínio não está incluído nos cálculos de orçamento da seção 2.3, criando falsa impressão de que SLA nunca contribui significativamente para a janela de contexto.

#### F.1.2. Corpus: mesma ressalva sistemática (planilhas subestimadas)
50 planilhas × 1.000 palavras é consistentemente subestimado em todas as 5 análises. Para SLA, relatórios mensais de performance em `.xlsx` podem ter histórico de SLAs medidos, incidentes, taxas de violação — dados tabulares densos que, serializados, excedem em muito 1.000 palavras.

---

### F.2. Pontos Fracos da Análise

#### F.2.1. SLA de disponibilidade do portal (99,5%/99%/98%) tratado como risco menor, mas é consulta frequente
A análise lista a "disponibilidade do portal omitida" como risco de baixa prioridade, mas incidentes de indisponibilidade do portal de tracking são **eventos de alta frequência e alta urgência** em operações logísticas. Um cliente Gold que não consegue acessar o portal abrirá chamado classificando como incidente crítico (carga com status desconhecido). O atendente precisará saber exatamente qual SLA de disponibilidade se aplica e como isso interage com os critérios de incidente crítico. O chunk SLA-2024-B que inclui disponibilidade de portal como linha adicional pode não ser suficiente — pode ser necessário um chunk SLA-2024-F dedicado a disponibilidade para cobrir queries específicas sobre uptime.

#### F.2.2. Gerente de conta dedicado (Gold) — caso de uso ausente nos exemplos
A tabela de SLA inclui "Gerente de conta dedicado: Sim" para Gold e "Não" para Silver/Standard. Queries como "tenho direito a um gerente de conta?", "quero falar com meu gerente dedicado" são comuns e semanticamente distantes de "SLA de resposta" ou "tempo de resolução". O chunk SLA-2024-A cobre os tiers mas não menciona gerente de conta — essa informação está na tabela principal (SLA-2024-B). A análise não discute se o chunking proposto garante que a linha de "gerente de conta" seja recuperada para esse tipo de query, criando **risco de omissão de benefício contratual** em respostas ao cliente Gold.

#### F.2.3. A condição de "relógio não pausa" para Gold crítico é mais complexa que indicada
A análise destaca corretamente que o relógio de SLA não pausa para incidentes críticos de clientes Gold. Mas a condição real no documento é dupla: (a) **horário comercial não se aplica** e (b) o incidente precisa ser **crítico** conforme os 4 critérios da seção 3 E (c) o cliente precisa ser **Gold**. Na prática, um incidente pode ser classificado como crítico por um atendente sem verificar se o cliente é Gold ou não — o que causaria aplicação errada do SLA 24/7 para um cliente Silver. A serialização do chunk SLA-2024-C precisa tornar a **tríplice condição** (Gold + crítico + sem pausa) explícita e inseparável, não apenas citar a exceção.

#### F.2.4. Penalidades: progressividade depende de contagem correta no mês
O chunk SLA-2024-E (Penalidades) descreve 3 níveis progressivos "no mesmo mês". Para o sistema RAG responder corretamente sobre penalidades, ele precisaria saber **quantas violações já ocorreram no mês atual** para o cliente em questão. Essa informação está no sistema de chamados (Azure DevOps), não na base documental. A análise não discute que queries sobre penalidades são parcialmente **não-respondíveis via RAG puro** sem integração com dados transacionais em tempo real — o LLM pode apenas explicar a regra, não aplicá-la ao caso concreto.

---

### F.3. Riscos Não Considerados

#### F.3.1. Versionamento anual do SLA — risco de coexistência com SLA-2025
A SLA-2024 está marcada como versão "2024.1", sugerindo um ciclo de atualização anual. Quando SLA-2025.1 for publicado, o pipeline enfrentará o mesmo problema de coexistência que PROC-042-v1 vs v2 — com o agravante de que os SLAs são **compromissos contratuais com implicação jurídica**. Informar a um cliente Gold que seu SLA de resposta é 2h quando o contrato atual diz 1h (hipotético) é um erro com consequência legal. A análise não propõe nenhuma estratégia de deprecação do SLA-2024 nem de migração para futuras versões.

#### F.3.2. "Não existem outros tiers" — cobertura insuficiente para variações de query
O chunk SLA-2024-A inclui `❌ NÃO EXISTEM outros tiers` explicitamente. Mas a alucinação de tiers inexistentes pode ser disparada por queries que usam termos como "Premium", "VIP", "Especial", "Plus", "Preferencial", "Exclusivo" — palavras que não aparecem no chunk e portanto têm baixa similaridade com ele. O embedding de "meu cliente é VIP" pode não recuperar SLA-2024-A com score suficiente para estar no Top-K, deixando o LLM sem a âncora negativa necessária. A estratégia de "negação explícita no chunk" é necessária mas não suficiente — precisa ser complementada com **query expansion ou sinônimos indexados** para variações comuns de tiers inexistentes.

#### F.3.3. Medição de SLA por Azure DevOps — o mensurando não está no contexto RAG
A seção 5 do SLA-2024 define que SLAs são medidos pelo Azure DevOps "a partir do timestamp de abertura do chamado". Um atendente que pergunte "o SLA foi violado?" precisaria saber: (a) qual é o timestamp de abertura do chamado, (b) qual o tier do cliente, (c) qual o tipo de chamado (geral ou crítico), e (d) se o relógio pausou fora do horário comercial. Nenhuma dessas informações está na base documental — estão no CRM/ticketing. O assistente RAG pode apenas **explicar a regra de cálculo**, não responder se um SLA específico foi violado. A análise não distingue claramente o que o assistente *pode* responder via RAG versus o que requer integração de sistema — criando expectativa incorreta sobre as capacidades do assistente.

#### F.3.4. Ausência de discussão sobre atualizações de SLA contratual por cliente
A SLA-2024 define os SLAs padrão, mas clientes podem ter SLAs **contratuais customizados** negociados pelo Comercial (a nota da seção 1 menciona "encaminhar ao Comercial para análise de viabilidade" para SLA fora dos tiers). Um cliente Silver com SLA customizado igual a Gold criaria uma situação onde o assistente informa o SLA errado com base na documentação padrão. A análise não discute a existência de exceções contratuais individuais nem como o pipeline seria informado sobre elas — um gap que poderia ser a maior fonte de respostas incorretas na prática.
