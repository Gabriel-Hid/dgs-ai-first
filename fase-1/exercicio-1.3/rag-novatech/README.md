# RAG Pipeline — Assistente de Atendimento NovaTech

Pipeline RAG mínimo para o assistente de atendimento da NovaTech Transportes.

## Stack

- **Python 3.10+**
- **ChromaDB** — vector store local
- **sentence-transformers** — embeddings open-source (`all-MiniLM-L6-v2`)
- **LangChain** — orquestração (opcional, usado para text splitting)

## Estrutura

```
rag-novatech/
├── dados/                    # Documentos .md da NovaTech (Anexo A)
├── chroma_db/                # Banco vetorial persistido (gerado pelo ingest)
├── config.py                 # Configurações centralizadas
├── ingest.py                 # Ingestão: chunking + embeddings + armazenamento
├── search.py                 # Busca: query → chunks mais similares
├── prompt_builder.py         # Montagem de prompt completo para LLM
├── main.py                   # Orquestrador / interface de teste
├── requirements.txt          # Dependências
└── README.md
```

## Como usar

### 1. Instalar dependências

```bash
pip install -r requirements.txt
```

### 2. Colocar documentos na pasta `dados/`

Copie os 5 arquivos .md da NovaTech para `dados/`:
- `FAQ-atendimento.md`
- `POL-001-politica-devolucao.md`
- `PROC-042-frete-especial-v1.md`
- `PROC-042-v2-frete-especial-revisado.md`
- `SLA-2024-tabela-sla-clientes.md`

### 3. Executar ingestão

```bash
python ingest.py
```

### 4. Testar busca e montagem de prompt

```bash
python main.py
```

## Estratégia de Chunking

A estratégia foi definida com base nas análises técnicas da Fase 1 (exercício 1.1):

| Documento | Estratégia | Justificativa |
|-----------|-----------|---------------|
| FAQ | 1 chunk por item (pergunta+resposta) | Itens independentes; query do atendente alinha com a pergunta do FAQ |
| POL-001 | Chunking semântico por seção + pair chunking 3.1+3.2 | Regra de exceção deve vir junto do prazo geral |
| PROC-042-v1 | Chunking por seção com metadado DEPRECATED | Evitar recuperação indevida para chamados novos |
| PROC-042-v2 | Chunking por seção com metadado CURRENT | Versão preferida para chamados >= 01/12/2023 |
| SLA-2024 | Chunking funcional por tipo de consulta | Alinhado ao padrão de pergunta do atendente |

## Validação

Use o mapa de cobertura do Anexo B para validar que o pipeline recupera os chunks corretos para cada pergunta tipo.
