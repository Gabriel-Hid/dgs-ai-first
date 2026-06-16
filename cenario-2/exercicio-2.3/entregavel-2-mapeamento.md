# Entregável 2 — Mapeamento de Criação e Consumo de Skills

> Exercício 2.3 · Estratégia de Skills · Visão de time: quem cria, quem consome, com que frequência

---

## Tabela Principal

| Skill | Nível | Frase-Ativação (gatilho para o agente) | Quem Cria | Quem Consome | Agentes | Frequência |
|---|---|---|---|---|---|---|
| `error-handling` | Foundation | "gera código que pode falhar", "escreve endpoint", "trata erro", "lança exceção" | Tech Lead | Todos os devs | Copilot + Claude (toda geração de código) | **Alta** |
| `typescript-conventions` | Foundation | "escreve arquivo `.ts`", "cria tipo", "define interface", "gera código TypeScript" | Tech Lead | Todos os devs | Copilot + Claude (toda geração de código) | **Alta** |
| `project-structure` | Foundation | "cria novo arquivo", "decide onde colocar", "organiza módulo", "estrutura pasta" | Tech Lead | Todos os devs | Copilot + Claude | **Média** |
| `azure-functions-endpoint` | Domain | "cria endpoint", "implementa handler HTTP", "novo Azure Function", "rota de API" | Dev Sênior | Devs backend | Copilot (alta frequência ao longo do projeto) | **Alta** |
| `azure-ai-search-integration` | Domain | "busca semântica", "chama AI Search", "vetor de embedding", "recupera chunks" | Dev Sênior | Devs backend | Copilot | **Alta** |
| `react-components` | Domain | "cria componente", "renderiza card", "painel web", "interface do usuário" | Dev (frontend) | Devs frontend | Copilot | **Média** |
| `testing-patterns` | Domain | "escreve teste", "cobre endpoint", "mock de serviço", "fixture de teste" | QA + Dev Sênior | QA + Devs | Copilot + Claude | **Alta** |
| `create-rag-endpoint` | Artifact | "novo endpoint RAG", "endpoint de consulta", "pipeline query → search → LLM" | Dev Sênior | Devs backend | Copilot (geração guiada, passo a passo) | **Alta** |
| `create-integration-test` | Artifact | "teste de integração para endpoint", "testar rota HTTP", "cenário de integração" | QA | QA + Devs | Copilot + Claude | **Alta** |
| `create-react-card` | Artifact | "card de resposta", "componente de resultado", "exibir resposta do assistente" | Dev (frontend) | Devs frontend | Copilot | **Média** |

---

## Detalhamento por Skill

### Foundation

#### `error-handling` · Foundation · ★ Principal
| Campo | Detalhe |
|---|---|
| **Frase-ativação** | Qualquer geração de código que envolva try/catch, handlers HTTP, chamadas externas (Azure, LLM) ou lançamento de exceções. |
| **Quem cria** | Tech Lead — define o contrato de erros do projeto e o mantém atualizado. |
| **Quem consome** | Todos os desenvolvedores (obrigatório); Product Specialist (para entender códigos de erro nas specs); QA (para testar cenários de erro). |
| **Agentes que usam** | GitHub Copilot (em toda sugestão inline que envolva catch/throw); Claude Code (ao gerar endpoints, serviços, testes). |
| **Frequência** | **Alta** — é lida antes de qualquer geração de código de lógica. |
| **Impacto se ausente** | Copilot gera `catch (e) {}` silencioso, erros genéricos sem código, stack traces expostos na resposta HTTP, mistura de `Error` nativo com `AppError`. |

#### `typescript-conventions` · Foundation
| Campo | Detalhe |
|---|---|
| **Frase-ativação** | Qualquer criação ou edição de arquivo `.ts`/`.tsx`. |
| **Quem cria** | Tech Lead. |
| **Quem consome** | Todos os desenvolvedores; todos os agentes. |
| **Agentes que usam** | Copilot + Claude (toda geração de código TypeScript). |
| **Frequência** | **Alta** — prerequisito universal. |
| **Impacto se ausente** | Copilot sugere `any`, omite `strict`, usa `require()` em vez de `import`, esquece extensão `.js` nos imports, usa `React.FC` desnecessário. |

#### `project-structure` · Foundation
| Campo | Detalhe |
|---|---|
| **Frase-ativação** | "Onde devo criar este arquivo?", criação de novo módulo, novo serviço, nova feature. |
| **Quem cria** | Tech Lead. |
| **Quem consome** | Todos os desenvolvedores; Delivery Manager (para entender onde está cada peça). |
| **Agentes que usam** | Copilot + Claude (ao sugerir localização de novos arquivos). |
| **Frequência** | **Média** — essencial no início; decresce após o time internalizar a estrutura. |
| **Impacto se ausente** | Copilot cria arquivos em lugares arbitrários, mistura `services/` com `functions/`, ignora separação `shared/` vs camadas específicas. |

---

### Domain

#### `azure-functions-endpoint` · Domain
| Campo | Detalhe |
|---|---|
| **Frase-ativação** | "Cria endpoint HTTP", "novo Azure Function trigger HTTP", "handler para rota". |
| **Quem cria** | Dev Sênior — responsável pela arquitetura de endpoints. |
| **Quem consome** | Devs backend; QA (para entender o contrato do endpoint ao testar); Tech Lead (revisão). |
| **Agentes que usam** | GitHub Copilot (autocomplete e geração de novo handler). |
| **Frequência** | **Alta** — o projeto tem múltiplos endpoints planejados (query, feedback, ingestão). |
| **Impacto se ausente** | Handler sem requestId, validação Zod omitida, logging com `console.log`, resposta sem tipagem `QueryOutput`. |

#### `azure-ai-search-integration` · Domain
| Campo | Detalhe |
|---|---|
| **Frase-ativação** | "Busca chunks", "chama Azure AI Search", "recupera documentos por embedding". |
| **Quem cria** | Dev Sênior. |
| **Quem consome** | Devs backend; Tech Lead (revisão de performance e cost); QA (mocks de search nos testes). |
| **Agentes que usam** | Copilot + Claude (geração de serviços de busca). |
| **Frequência** | **Alta** — toda query RAG passa pelo search. |
| **Impacto se ausente** | Credentials hardcoded, `minScore` ignorado, `SearchChunk` tipado como `any`, sem wrap em `SearchServiceError`. |

#### `react-components` · Domain
| Campo | Detalhe |
|---|---|
| **Frase-ativação** | "Cria componente React", "renderiza card de resposta", "componente do painel". |
| **Quem cria** | Dev frontend. |
| **Quem consome** | Devs frontend; QA (testes de componente); Product Specialist (para revisar UX nos PRs). |
| **Agentes que usam** | Copilot (inline autocomplete de JSX). |
| **Frequência** | **Média** — painel web é uma feature específica (não toda task envolve UI). |
| **Impacto se ausente** | `React.FC` com genérico explícito desnecessário, props sem tipo definido, sem acessibilidade ARIA, estado mutável direto em props. |

#### `testing-patterns` · Domain
| Campo | Detalhe |
|---|---|
| **Frase-ativação** | "Escreve teste", "cobre com unit test", "mock de dependência", "teste de erro". |
| **Quem cria** | QA + Dev Sênior — parceria QA define padrão, dev refina para a stack. |
| **Quem consome** | QA (automação); Devs (TDD/testes locais); Tech Lead (revisão de cobertura). |
| **Agentes que usam** | Copilot + Claude (geração de testes ao lado de implementação). |
| **Frequência** | **Alta** — acompanha toda nova implementação. |
| **Impacto se ausente** | `vi.mock` mal configurado, fixtures inline em vez de `tests/fixtures/`, testes que passam sem assertions reais (`expect(true).toBe(true)`), sem teste de caminho de erro. |

---

### Artifact

#### `create-rag-endpoint` · Artifact
| Campo | Detalhe |
|---|---|
| **Frase-ativação** | "Cria endpoint RAG", "implementa pipeline query-search-LLM", "novo endpoint de consulta ao assistente". |
| **Quem cria** | Dev Sênior — define a receita canônica do pipeline RAG. |
| **Quem consome** | Devs backend (execução); Product Specialist (entender o fluxo para specs); Tech Lead (revisão). |
| **Agentes que usam** | GitHub Copilot (geração guiada do handler completo). |
| **Frequência** | **Alta** — é o artefato central do projeto; repetido para cada novo endpoint. |
| **Impacto se ausente** | Pipeline incompleto (falta etapa de embedding ou de confidence check), `source_document` ausente (viola guardrail VC-02), sem logging por etapa do pipeline. |

#### `create-integration-test` · Artifact
| Campo | Detalhe |
|---|---|
| **Frase-ativação** | "Teste de integração para este endpoint", "testa rota HTTP completa", "cobre cenários de erro no endpoint". |
| **Quem cria** | QA — é o dono da estratégia de testes de integração. |
| **Quem consome** | QA + Devs backend; CI/CD (executa os testes). |
| **Agentes que usam** | Copilot + Claude (geração do arquivo de teste ao lado do endpoint). |
| **Frequência** | **Alta** — criado junto com cada `create-rag-endpoint`. |
| **Impacto se ausente** | Teste sem fixture de request/response, mocks de Azure AI Search ausentes, sem cobertura de caminho de erro (`ValidationError`, `LlmServiceError`). |

#### `create-react-card` · Artifact
| Campo | Detalhe |
|---|---|
| **Frase-ativação** | "Cria card de resposta", "componente para exibir resultado do assistente", "card com answer, confidence e source". |
| **Quem cria** | Dev frontend. |
| **Quem consome** | Devs frontend; Product Specialist (valida visualmente nos PRs). |
| **Agentes que usam** | Copilot (geração de JSX+TypeScript do card). |
| **Frequência** | **Média** — uma a duas vezes por sprint de UI. |
| **Impacto se ausente** | Campo `source_document` omitido no card (viola UX de transparência), `warning` não renderizado quando `confidence === 'low'`, sem tipagem `QueryOutput`. |

---

## Visão de Time (quem usa skills além dos devs)

| Papel | Skills relevantes | Contexto de uso |
|---|---|---|
| **Tech Lead** | Todas as Foundation; todas as Domain | Criação e revisão; define os padrões que o resto referencia |
| **Dev Sênior** | Foundation + Domain + Artifact (`create-rag-endpoint`) | Implementação de features backend e mentoria de devs |
| **Dev Backend** | `error-handling`, `typescript-conventions`, `azure-functions-endpoint`, `azure-ai-search-integration`, `create-rag-endpoint`, `create-integration-test` | Implementação diária com Copilot |
| **Dev Frontend** | `typescript-conventions`, `react-components`, `create-react-card` | Implementação do painel web |
| **QA** | `testing-patterns`, `create-integration-test`, `error-handling` | Automação de testes; valida cobertura de cenários de erro |
| **Product Specialist (PS)** | `project-structure` (para localizar docs), `create-rag-endpoint` (para entender o pipeline) | Leitura para embasar specs; entender fluxo sem código |
| **Delivery Manager** | `project-structure` | Entender organização do repositório; escopo de entregas |

---

## Resumo de Frequência

| Frequência | Skills |
|---|---|
| **Alta** | `error-handling`, `typescript-conventions`, `azure-functions-endpoint`, `azure-ai-search-integration`, `testing-patterns`, `create-rag-endpoint`, `create-integration-test` |
| **Média** | `project-structure`, `react-components`, `create-react-card` |
| **Baixa** | — (nenhuma skill foi incluída sem uso justificado) |
