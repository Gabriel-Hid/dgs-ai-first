# Entregável 1 — Árvore de Skills do NovaTech Assistant

> Exercício 2.3 · Estratégia de Skills · Hierarquia Foundation → Domain → Artifact

---

## Visão Geral da Hierarquia

```
skills/
├── foundation/                        # Convenções globais — lidas por TODAS as outras skills
│   ├── error-handling.md              ★ SKILL PRINCIPAL (base de tudo)
│   ├── typescript-conventions.md
│   └── project-structure.md
│
├── domain/                            # Padrões por camada/tecnologia
│   ├── azure-functions-endpoint.md    # Estrutura de endpoints HTTP no Azure Functions v4
│   ├── azure-ai-search-integration.md # Integração com Azure AI Search (vector + hybrid)
│   ├── react-components.md            # Componentes React do painel web
│   └── testing-patterns.md           # Padrões de teste (unit, integration, e2e)
│
└── artifact/                          # Receitas de geração de artefatos específicos
    ├── create-rag-endpoint.md         # Criar endpoint de consulta RAG completo
    ├── create-integration-test.md     # Criar teste de integração para endpoint
    └── create-react-card.md          # Criar card React de resposta do assistente
```

---

## Foundation (3 skills)

### `error-handling.md` ★ — Mais importante
- **Propósito:** Define como todos os erros são representados, propagados e respondidos.
- **Ancora:** Classe `AppError` em `src/shared/errors.ts`, função `toErrorResponse`.
- **Referenciada por:** todas as skills de Domain e Artifact; lida em toda geração de código.
- **Raiz de padrão:** nunca vazar stack trace para o caller; usar códigos semânticos (`VALIDATION_ERROR`, `LLM_SERVICE_ERROR`); `catch (e) {}` silencioso é antipadrão proibido.

### `typescript-conventions.md`
- **Propósito:** Convenções de TypeScript para o projeto — modo strict, tipagem, proibições.
- **Ancora:** `tsconfig.json` (`"strict": true`, `"target": "ES2022"`), imports com `.js`, sem `any`.
- **Referenciada por:** todas as skills; é prerequisito de qualquer geração de código TypeScript.

### `project-structure.md`
- **Propósito:** Layout de diretórios, responsabilidade de cada pasta, regras de import entre camadas.
- **Ancora:** `src/` (functions, services, shared, types, web, bot, pipeline), `tests/` (unit, integration, e2e, fixtures).
- **Referenciada por:** `azure-functions-endpoint`, `react-components`, `create-rag-endpoint`.

---

## Domain (4 skills)

### `azure-functions-endpoint.md`
- **Propósito:** Estrutura canônica de um endpoint Azure Functions v4 (trigger HTTP, validação Zod, logging com requestId, resposta tipada).
- **Ancora:** `src/functions/`, `src/shared/types.ts` (schemas Zod), `src/shared/logger.ts`.
- **Reusa Foundation:** `error-handling`, `typescript-conventions`.
- **Raiz de padrão:** handler async exportado, requestId gerado por chamada, validação Zod antes de qualquer lógica, resposta sempre `QueryOutput`.

### `azure-ai-search-integration.md`
- **Propósito:** Como consumir o Azure AI Search (vector search, hybrid, tratamento de score).
- **Ancora:** `src/services/`, `src/shared/config.ts` (`azure.search.*`), `src/shared/types.ts` (`SearchChunk`).
- **Reusa Foundation:** `error-handling` (wrap em `SearchServiceError`), `typescript-conventions`.
- **Raiz de padrão:** `minScore` como threshold, sempre retornar `SearchChunk[]`, nunca injetar credentials no código.

### `react-components.md`
- **Propósito:** Estrutura de componentes React do painel web (cards, formulários, hooks).
- **Ancora:** `src/web/`, convenções de named export, sem prop drilling, TypeScript strict.
- **Reusa Foundation:** `typescript-conventions`, `error-handling` (boundary de erro no React).
- **Raiz de padrão:** componentes funcionais, props tipadas com `interface`, sem `React.FC`, acessibilidade ARIA básica.

### `testing-patterns.md`
- **Propósito:** Estrutura e convenções de testes — unit com Vitest, integration, fixtures.
- **Ancora:** `vitest.config.ts`, `tests/unit/`, `tests/integration/`, `tests/fixtures/`.
- **Reusa Foundation:** `typescript-conventions`, `error-handling` (testar erros tipados).
- **Raiz de padrão:** `describe/it` aninhado por módulo, `vi.mock` para dependências externas, fixtures em `tests/fixtures/`, sem `any` nos tipos de mock.

---

## Artifact (3 skills)

### `create-rag-endpoint.md`
- **Propósito:** Receita passo a passo para gerar um endpoint RAG completo: schema Zod → validação → embedding → search → LLM → resposta.
- **Reusa Domain:** `azure-functions-endpoint`, `azure-ai-search-integration`.
- **Reusa Foundation:** `error-handling`, `typescript-conventions`.
- **Frequência:** Alta — um endpoint novo a cada feature do assistente.

### `create-integration-test.md`
- **Propósito:** Receita para criar teste de integração de endpoint: setup de mocks, chamada HTTP, asserções de schema Zod.
- **Reusa Domain:** `testing-patterns`, `azure-functions-endpoint`.
- **Reusa Foundation:** `error-handling` (testar cenários de erro), `typescript-conventions`.
- **Frequência:** Alta — acompanha cada endpoint gerado com `create-rag-endpoint`.

### `create-react-card.md`
- **Propósito:** Receita para criar card React de resposta (exibe `answer`, `confidence`, `source_document`, `warning` opcional).
- **Reusa Domain:** `react-components`.
- **Reusa Foundation:** `typescript-conventions`.
- **Frequência:** Média — para cada nova feature do painel web.

---

## Mapa de Dependências (grafo simplificado)

```
create-rag-endpoint ──► azure-functions-endpoint ──► error-handling ★
       │                                         └──► typescript-conventions
       └──────────────► azure-ai-search-integration ► error-handling ★

create-integration-test ──► testing-patterns ──────► typescript-conventions
                        └──► azure-functions-endpoint

create-react-card ──────► react-components ──────────► typescript-conventions
                                           └──────────► error-handling ★
```

`error-handling` ★ é a única skill referenciada diretamente por **todas** as demais.
Por isso é a Foundation principal a ser escrita com o nível de detalhe mais alto.

---

## Validação de Coerência

| Skill | Artefato recorrente que motiva | Existe no projeto? |
|---|---|---|
| `error-handling` | Toda resposta HTTP de erro, `AppError`, `toErrorResponse` | ✅ `src/shared/errors.ts` |
| `typescript-conventions` | Todo arquivo `.ts` gerado | ✅ `tsconfig.json`, `src/shared/types.ts` |
| `project-structure` | Toda decisão de onde criar novo arquivo | ✅ layout `src/` / `tests/` |
| `azure-functions-endpoint` | Cada novo endpoint em `src/functions/` | ✅ pasta existe |
| `azure-ai-search-integration` | Cada chamada ao Azure AI Search em `src/services/` | ✅ `SearchChunk`, `config.azure.search` |
| `react-components` | Cada componente em `src/web/` | ✅ pasta existe |
| `testing-patterns` | Cada arquivo em `tests/unit/` e `tests/integration/` | ✅ `vitest.config.ts` |
| `create-rag-endpoint` | Cada endpoint RAG novo (query, feedback, etc.) | ✅ padrão estabelecido |
| `create-integration-test` | Acompanha cada `create-rag-endpoint` | ✅ `tests/integration/` |
| `create-react-card` | Cards de resposta, feedback UI | ✅ `src/web/` |

**Conclusão:** Todas as 10 skills mapeiam a artefatos ou padrões reais do repositório. Nenhuma skill órfã.
