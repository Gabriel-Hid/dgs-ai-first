# Documentação Técnica — Pipeline RAG NovaTech

**Projeto:** Assistente de Atendimento NovaTech (Prova de Conceito)  
**Exercício:** Fase 1 — Exercício 1.3 (Desenvolvedor)  
**Data:** 02/06/2026  
**Stack:** Python 3.12 + ChromaDB + sentence-transformers  

---

## 1. Visão Geral da Arquitetura

O pipeline é composto por 4 módulos Python com responsabilidades distintas, seguindo o fluxo clássico de RAG:

```
┌─────────────┐    ┌─────────────┐    ┌──────────────────┐    ┌──────────────┐
│  ingest.py  │ →  │  search.py  │ →  │ prompt_builder.py│ →  │   main.py    │
│ (Ingestão)  │    │  (Busca)    │    │ (Montagem)       │    │ (Orquestrador)│
└─────────────┘    └─────────────┘    └──────────────────┘    └──────────────┘
       ↓                  ↑                                          ↑
┌─────────────┐    ┌─────────────┐                           ┌──────────────┐
│ dados/*.md  │    │  chroma_db/ │                           │  config.py   │
│ (5 docs)    │    │ (27 chunks) │                           │ (Configuração)│
└─────────────┘    └─────────────┘                           └──────────────┘
```

---

## 2. Stack Tecnológica e Justificativas

| Componente | Tecnologia | Justificativa |
|-----------|-----------|---------------|
| Linguagem | Python 3.12 | Ecossistema maduro para ML/NLP, tipagem moderna com `dict | None` |
| Vector Store | ChromaDB 1.5.9 (PersistentClient) | Open-source, zero config, persistência local, API simples |
| Embeddings | sentence-transformers (`all-MiniLM-L6-v2`) | Modelo leve (384 dims), bom equilíbrio custo/qualidade, roda sem GPU |
| Similaridade | Cosseno (`hnsw:space: cosine`) | Padrão para embeddings normalizados; escala 0–1 intuitiva |
| LLM | Externo (Claude/ChatGPT via chat manual) | PoC sem custo de API; prompt gerado → colado manualmente |
| Formato docs | Markdown (.md) | Estruturação semântica nativa com headers; fácil de parsear com regex |

**Decisão: não usar LangChain.** O pipeline foi implementado com código manual (sem frameworks de orquestração) para:
- Controle total sobre a estratégia de chunking por documento
- Transparência no fluxo de dados (sem abstrações opacas)
- Menor número de dependências (apenas `chromadb` + `sentence-transformers`)

---

## 3. Estratégia de Chunking

### 3.1. Filosofia Geral

A estratégia de chunking é **semântica e orientada por documento**, não baseada em tamanho fixo. Cada documento tem uma função de chunking dedicada porque:

1. Os documentos têm estruturas internas diferentes (FAQ = itens independentes; POL = seções hierárquicas; SLA = tabelas por tier)
2. As queries dos atendentes são curtas e específicas ("Qual o prazo de devolução?") — chunks pequenos (100–300 tokens) maximizam a precisão do retrieval
3. Chunks devem ser **unidades semânticas auto-contidas** — cada chunk deve fazer sentido isoladamente

### 3.2. Chunking por Documento

| Documento | Função | Estratégia | Chunks | Tamanho médio |
|-----------|--------|-----------|--------|---------------|
| FAQ-Atendimento | `chunk_faq()` | 1 chunk por item (regex `### Item N`) | 9 | ~80 tokens |
| POL-001 | `chunk_pol001()` | 1 chunk por seção (3.1, 3.2, 3.3, 3.5) | 4 | ~150 tokens |
| PROC-042-v1 | `chunk_proc042(v1)` | 1 chunk por seção (fórmula, multiplicadores, prazo, condições) | 4 | ~120 tokens |
| PROC-042-v2 | `chunk_proc042(v2)` | Idem + chunk de transição (seção 5) | 5 | ~120 tokens |
| SLA-2024 | `chunk_sla2024()` | Chunking funcional por tipo de consulta | 5 | ~130 tokens |
| **Total** | — | — | **27** | ~120 tokens |

### 3.3. Detalhes por Documento

#### FAQ-Atendimento (9 chunks)
- **Lógica:** Cada item é semanticamente independente — a pergunta e a resposta formam uma unidade completa.
- **Regex:** `r'### Item (\d+)\s*[—\-]\s*[""](.+?)["]\s*\n(.*?)(?=### Item \d+|$)'`
- **IDs:** Usam o número real do item (ex: `FAQ-03`, `FAQ-08`, `FAQ-15`), não numeração sequencial. Isso alinha com o Anexo B de referência.
- **Conteúdo do chunk:** Inclui título do item como cabeçalho para melhorar o matching semântico.

#### POL-001 — Política de Devolução (4 chunks)
- **Lógica:** Cada seção contém uma regra de negócio distinta (prazo, exceções, procedimento, custos).
- **Enriquecimento semântico:** Os chunks A e B possuem palavras-chave injetadas:
  - POL-001-A: `"prazo devolução, devolver mercadoria, dias úteis, prazo para devolver"`
  - POL-001-B: `"carga perigosa devolução, devolver carga perigosa, exceção devolução, não elegível, ANTT"`
- **Justificativa do enriquecimento:** O modelo de embedding `all-MiniLM-L6-v2` é generalista (treinado em inglês). Palavras-chave em português reforçam a similaridade com queries típicas dos atendentes.
- **Decisão: seções 3.1 e 3.2 separadas (não pair-chunked).** O Anexo B de referência define POL-001-A e POL-001-B como chunks distintos. Manter separados permite que cada um apareça no ranking independentemente.

#### PROC-042 v1/v2 — Frete Especial (4+5 chunks)
- **Lógica:** Cada seção é um parâmetro independente do cálculo de frete (fórmula, multiplicadores, prazo, condições).
- **Versionamento explícito:** Todo chunk inclui cabeçalho com versão e status:
  ```
  [PROC-042 | Versão: v2 | Status: ✅ VERSÃO ATUAL]
  [PROC-042 | Versão: v1 | Status: ⚠️ SUBSTITUÍDO por PROC-042-v2]
  ```
- **IDs diferenciados:** v1 usa prefixo `PROC-042-` (ex: `PROC-042-A`), v2 usa `PROC-042v2-` (ex: `PROC-042v2-A`). Alinhado com Anexo B.
- **Chunk exclusivo v2 (PROC-042v2-E):** Disposições transitórias — regra de decisão sobre qual versão usar. Chunk de prioridade crítica para evitar mistura de multiplicadores.

#### SLA-2024 — Tabela de SLA (5 chunks)
- **Lógica:** Chunking funcional orientado pelo tipo de query do atendente, não pela estrutura tabular do documento.
- **Serialização de tabelas:** Em vez de manter tabelas em formato tabular (difícil para embeddings), os dados são serializados em formato legível:
  ```
  GOLD:     1ª resposta → até 2h úteis | Resolução → até 24h úteis
  SILVER:   1ª resposta → até 4h úteis | Resolução → até 48h úteis
  ```
- **Enriquecimento do chunk A:** Inclui nota explícita `"NÃO existem outros tiers além de Gold, Silver e Standard. Não existe tier Platinum, Diamond ou Premium."` para maximizar retrieval em queries sobre tiers inexistentes.
- **Separação chamados gerais vs. incidentes críticos (chunks B e C):** Evita que o LLM misture SLAs de contextos diferentes (Liu et al., 2023 — efeito "Lost in the Middle").

### 3.4. Justificativa: Por que NÃO usar chunking fixo (512 tokens)?

| Aspecto | Chunking fixo (512 tokens) | Chunking semântico (implementado) |
|---------|---------------------------|-----------------------------------|
| Fronteiras | Corta no meio de frases/tabelas | Respeita limites lógicos de seção |
| Contexto | Chunk pode misturar temas | 1 tema = 1 chunk |
| Retrieval | Query genérica → chunks parciais | Query específica → chunk completo |
| Manutenção | Difícil de debugar | Chunks nomeados e rastreáveis |
| Alinhamento Anexo B | Impossível | IDs idênticos ao gabarito |

---

## 4. Modelo de Embedding

### 4.1. Escolha: `all-MiniLM-L6-v2`

| Propriedade | Valor |
|-------------|-------|
| Dimensões | 384 |
| Modelo base | MiniLM (Microsoft) |
| Treinamento | Sentence pairs em inglês (SBERT) |
| Tamanho | ~80 MB |
| Velocidade | ~14.000 sentenças/segundo (CPU) |
| Suporte GPU | Opcional (funciona em CPU para 27 chunks) |

**Trade-offs da escolha:**
- ✅ Leve e rápido (CPU-only viável para PoC)
- ✅ Gratuito e open-source
- ✅ Qualidade suficiente para queries curtas em domínio restrito
- ⚠️ Treinado em inglês — menor performance para português
- ⚠️ 384 dims = menor capacidade semântica que modelos maiores (768/1024 dims)

**Mitigação para limitação de idioma:** Enriquecimento de chunks com palavras-chave em português (seção 3.3) e cabeçalhos descritivos que reforçam o match.

### 4.2. Padrão Singleton

O modelo é carregado uma única vez e reutilizado (`get_model()` em `search.py`). Isso evita re-carregamento de ~80 MB a cada query no modo interativo.

---

## 5. Armazenamento Vetorial (ChromaDB)

### 5.1. Configuração

| Parâmetro | Valor | Justificativa |
|-----------|-------|---------------|
| Client | `PersistentClient` | Persiste dados em disco (pasta `chroma_db/`) |
| Métrica | `cosine` (`hnsw:space`) | Padrão para embeddings normalizados; score interpretável (0–1) |
| Collection | `novatech_docs` | Coleção única com todos os chunks |
| Índice | HNSW (padrão ChromaDB) | Busca aproximada eficiente para poucos vetores |

### 5.2. Metadados Armazenados

Cada chunk possui metadados que permitem filtragem pós-retrieval:

```python
{
    "source": "POL-001",           # Documento de origem
    "type": "normativo",           # Tipo: contratual, normativo, procedimento, informal
    "authority": "alta",           # Nível de autoridade: maxima, alta, baixa
    "version_status": "current",   # Status: current, deprecated
    "version": "3.1",             # Versão do documento
    "date": "2024-01-15",         # Data da última atualização
    "chunk_id": "POL-001-A",      # ID do chunk
    "section": "3.1",             # Seção do documento
    "topic": "prazo-devolucao",   # Tópico semântico
}
```

### 5.3. Filtro de Versão

A função `search_with_version_filter()` implementa filtragem no ChromaDB:
- **`prefer_current=True` (padrão):** Filtra `version_status = "current"`, excluindo chunks da PROC-042-v1 (deprecated)
- **`prefer_current=False`:** Retorna todos os chunks (útil para chamados anteriores a 01/12/2023)

Isso implementa a recomendação das análises técnicas (exercício 1.1) de evitar que o contexto contenha chunks contraditórios de v1 e v2 simultaneamente.

---

## 6. Busca e Retrieval

### 6.1. Parâmetros

| Parâmetro | Valor | Justificativa |
|-----------|-------|---------------|
| Top-K | 5 | Equilíbrio entre cobertura e foco; 5–8 recomendado para evitar "Lost in the Middle" |
| Métrica | Similaridade cosseno | `score = 1 - distance` (ChromaDB retorna distância) |
| Filtro | `version_status = "current"` | Exclui docs deprecated por padrão |

### 6.2. Fluxo de Busca

```
Query (texto) → encode(model) → embedding (384 dims) → ChromaDB.query()
     → top-K docs ordenados por distância cosseno → conversão para score
     → lista[{id, content, metadata, distance, score}]
```

### 6.3. Conversão de Score

ChromaDB retorna **distância** cosseno (0 = idêntico, 2 = oposto). O pipeline converte para **similaridade**:
```python
similarity_score = 1 - distance  # Range: -1 a 1 (na prática 0.4 a 0.7 para este corpus)
```

---

## 7. Montagem do Prompt

### 7.1. Estrutura e Ordem de Injeção

A ordem dos componentes no prompt segue a recomendação para mitigar "Lost in the Middle" (Liu et al., 2023):

```
┌──────────────────────────────────────────────────┐
│ 1. SYSTEM PROMPT (estático)           ← INÍCIO   │  ~2.000 tokens
│    - Identidade, hierarquia, guardrails, formato │
├──────────────────────────────────────────────────┤
│ 2. DADOS DO CLIENTE (dinâmico)                   │  ~50 tokens
│    - Tier, nº contrato                           │
├──────────────────────────────────────────────────┤
│ 3. CONTEXTO RECUPERADO (dinâmico)                │  ~500-1500 tokens
│    - Chunks RAG ordenados por score decrescente  │
│    - Cada chunk com: ID, score, fonte, status    │
├──────────────────────────────────────────────────┤
│ 4. PERGUNTA DO ATENDENTE (dinâmico)   ← FINAL   │  ~50 tokens
└──────────────────────────────────────────────────┘
```

**Justificativa da ordem:**
- System prompt no início → máxima atenção do modelo (instruções críticas)
- Pergunta no final → modelo "lembra" do que está sendo perguntado ao gerar resposta
- Chunks no meio → ordenados por score decrescente para que os mais relevantes fiquem mais próximos do início

### 7.2. Orçamento de Contexto

| Componente | Tokens estimados | % do total |
|-----------|-----------------|-----------|
| System prompt (7 guardrails + formato + hierarquia) | ~2.000 | 61% |
| Dados do cliente | ~50 | 2% |
| 5 chunks recuperados (avg 120 tokens + metadata) | ~800 | 24% |
| Pergunta do atendente | ~50 | 2% |
| Buffer para resposta | ~350 | 11% |
| **Total por query** | **~3.250** | 100% |

O prompt completo (~3.250 tokens) cabe confortavelmente em qualquer modelo moderno (GPT-4o: 128K, Claude: 200K).

### 7.3. Formato de Chunk no Contexto

Cada chunk é apresentado ao LLM com metadados de rastreabilidade:
```
PROC-042v2-B [score: 0.543 | fonte: PROC-042-v2 | status: current]:
"[PROC-042 | Versão: v2 | Status: ✅ VERSÃO ATUAL]
[Seção 2.1: Multiplicadores regionais]
..."
```

Isso permite que o LLM:
- Identifique a fonte para citação (REGRA 1 do guardrail)
- Resolva conflitos de versão (hierarquia de fontes)
- Avalie a confiabilidade (authority: maxima vs. baixa)

---

## 8. System Prompt

### 8.1. Componentes Estáticos (~2.000 tokens)

| Seção | Conteúdo | Tokens |
|-------|----------|--------|
| Identidade e papel | Assistente interno, não voltado ao cliente final | ~100 |
| Hierarquia de fontes | SLA > POL > PROC-v2 > PROC-v1 > FAQ | ~250 |
| Guardrails (7 regras) | Citação, não-invenção, escalação, tiers, cargas perigosas, cobertura, FAQ | ~700 |
| Formato de resposta | Estrutura [RESPOSTA DIRETA] + [DETALHAMENTO] + [FONTE(S)] + [AÇÃO] | ~300 |
| Instruções para uso de chunks | 6 regras de como interpretar o contexto recuperado | ~250 |

### 8.2. Guardrails Implementados

| # | Guardrail | Enforcement |
|---|-----------|-------------|
| 1 | Citação obrigatória de fontes | Probabilístico (no prompt) |
| 2 | Proibição de invenção de dados | Probabilístico (no prompt) |
| 3 | Informação não encontrada → escalar | Probabilístico (no prompt) |
| 4 | Tiers inexistentes → alertar | Probabilístico (no prompt) |
| 5 | Cargas perigosas → exceção devolução | Probabilístico (no prompt) |
| 6 | Tópicos sem cobertura → escalar | Probabilístico (no prompt) |
| 7 | FAQ como fonte → alerta obrigatório | Probabilístico (no prompt) |

> **Nota:** Todos os guardrails são probabilísticos (implementados no prompt). Em produção, recomenda-se complementar com validação determinística pós-geração (ex: regex para verificar presença de "(Fonte: ...)" na resposta).

---

## 9. Orquestração (main.py)

### 9.1. Modos de Execução

| Modo | Comando | Descrição |
|------|---------|-----------|
| Interativo | `python main.py` | Loop pergunta → busca → prompt completo para clipboard |
| Teste batch | `python main.py test` | Executa 8 queries do Anexo B e valida retrieval |
| Ingestão | `python main.py ingest` | Re-executa ingestão de documentos |

### 9.2. Comandos Interativos

| Comando | Efeito |
|---------|--------|
| `tier GOLD\|SILVER\|STANDARD` | Define tier do cliente para inclusão no contexto |
| `topk N` | Altera número de chunks recuperados |
| `ingest` | Re-executa pipeline de ingestão |
| `sair` | Encerra o programa |

### 9.3. Auto-verificação de Pré-requisitos

O `main.py` verifica automaticamente:
1. Existência da pasta `dados/` com arquivos `.md`
2. Existência do `chroma_db/` — se ausente, executa ingestão automaticamente

---

## 10. Resultados de Validação

### 10.1. Teste Batch (8 queries do Anexo B)

| # | Query | Chunk(s) esperado(s) | Recuperado? |
|---|-------|---------------------|-------------|
| 1 | "Qual o prazo de devolução?" | POL-001-A, POL-001-B | ✅ |
| 2 | "Posso devolver carga perigosa?" | POL-001-B | ✅ |
| 3 | "Qual o SLA do cliente Gold?" | SLA-2024-B | ✅ |
| 4 | "Qual o SLA do cliente Platinum?" | SLA-2024-A | ✅ |
| 5 | "Frete para 600kg para Manaus?" | PROC-042v2-B, PROC-042v2-A | ⚠️ Parcial |
| 6 | "Qual o multiplicador para o Sudeste?" | PROC-042v2-B | ✅ |
| 7 | "O que acontece com carga danificada?" | FAQ-38 | ✅ |
| 8 | "Carga perigosa com frete expresso?" | FAQ-32 | ✅ |

**Resultado: 8/8 queries com ao menos um chunk correto no Top-5.**

> ⚠️ Query 5 ("Frete para 600kg para Manaus?"): PROC-042v2-A recuperado mas PROC-042v2-B (multiplicadores) ficou fora do Top-5 em testes manuais expandidos. Causa: embedding de "Manaus" não se aproxima semanticamente de "Norte".

### 10.2. Limitações Identificadas

| Limitação | Causa raiz | Impacto | Proposta de mitigação |
|-----------|-----------|---------|----------------------|
| Queries com nomes de cidades não recuperam multiplicadores regionais | Embedding não faz mapeamento geográfico | Resposta incompleta | Enriquecer chunks com nomes de cidades/estados |
| FAQ-41 aparece em muitas queries (irrelevante) | Chunk genérico sobre SLA com alta sobreposição semântica | Slot desperdiçado no Top-K | Implementar re-ranking por autoridade |
| Scores baixos (0.40–0.60) | Modelo treinado em inglês; corpus em português | Dificuldade de definir threshold | Considerar modelo multilíngue para produção |

---

## 11. Estrutura de Arquivos

```
rag-novatech/
├── config.py              # Configuração centralizada (paths, model, prompt, metadados)
├── ingest.py              # Pipeline de ingestão: leitura → chunking → embedding → ChromaDB
├── search.py              # Busca semântica com filtro de versão
├── prompt_builder.py      # Montagem do prompt completo (system + contexto + pergunta)
├── main.py                # Orquestrador: modo interativo + batch test
├── dados/                 # 5 documentos .md da NovaTech (fonte)
│   ├── FAQ-atendimento.md
│   ├── POL-001-politica-devolucao.md
│   ├── PROC-042-frete-especial-v1.md
│   ├── PROC-042-v2-frete-especial-revisado.md
│   └── SLA-2024-tabela-sla-clientes.md
└── chroma_db/             # Armazenamento persistente ChromaDB (27 chunks)
```

---

## 12. Dependências

```
chromadb==1.5.9
sentence-transformers==5.5.1
```

Instalação:
```bash
python -m pip install chromadb sentence-transformers --only-binary=:all:
```

> `--only-binary=:all:` evita necessidade de C++ Build Tools (wheel pré-compilado do `chroma-hnswlib`).
