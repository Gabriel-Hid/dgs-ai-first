# Exercício 2.3 — Definição de estratégia de skills do projeto

> Papel: **Desenvolvedor** · Ferramentas: **Claude (chat) + GitHub Copilot**
> Cenário-Âncora 2 — Fase de Estruturação do Trabalho (NovaTech Assistant)

---

## 1. Resumo

O desenvolvedor precisa definir a **estratégia de skills** do projeto: quais skills existem,
como se organizam na hierarquia **Foundation → Domain → Artifact**, **quem cria** e **quem
consome** cada uma, e a frequência de uso estimada. Depois, com o GitHub Copilot, escrever o
`SKILL.md` da **skill Foundation mais importante** — aquela que serve de base para todas as
outras — contendo contexto, regras prescritivas, exemplos concretos (DO/DON'T com código) e
anti-padrões.

Skills são o mecanismo que faz os agentes gerarem **outputs consistentes** com os padrões do
projeto, em vez de código genérico.

---

## 2. Contexto

O repositório (Anexo C / Anexo D) já reserva a árvore de skills em `skills/` com três níveis:

```
skills/
├── foundation/   # convenções globais (base de tudo)
│   ├── typescript-conventions.md
│   ├── error-handling.md
│   └── project-structure.md
├── domain/       # padrões por camada
│   ├── azure-functions-endpoint.md
│   ├── azure-ai-search-integration.md
│   ├── react-components.md
│   └── testing-patterns.md
└── artifact/     # receitas de geração específicas
    ├── create-rag-endpoint.md
    ├── create-integration-test.md
    └── create-react-card.md
```

No starter repo esses arquivos existem mas estão **vazios** — definir a estratégia e
escrever a Foundation principal é a tarefa.

### Artefatos produzidos repetidamente no projeto (input)
- Endpoints Azure Functions com padrão RAG (vários ao longo do projeto).
- Testes de integração para endpoints (mesmo padrão para todos).
- Componentes React para o painel web (cards de resposta, formulários de feedback).
- Documentação técnica de endpoints (ADRs, READMEs de módulo).
- Specs de produto (seguindo template SDD).

---

## 3. Por que fazer

- **Repetição sem skill = inconsistência.** Se cada endpoint RAG for gerado "do zero" pelo
  agente, cada um sai com um estilo de erro, logging e validação diferente. Skills
  cristalizam o padrão uma vez e o replicam.
- **Skills são conhecimento reutilizável e versionado.** Diferente de um prompt jogado no
  chat, a skill vive no repositório, evolui com o projeto e é lida por qualquer agente.
- **Hierarquia evita duplicação.** A Foundation define o que vale para tudo (TS, erros,
  logging); Domain e Artifact apenas referenciam, sem repetir. Mudou a regra de logging?
  Muda só na Foundation.
- **Visão de time, não só de dev.** A atribuição de criação/consumo mostra que skills servem
  PS (template SDD), QA (testing-patterns) e devs (endpoints/componentes) — não são só para
  quem escreve código.

---

## 4. O que precisa ser feito

1. **Definir a árvore de skills (com Claude)** seguindo Foundation → Domain → Artifact:
   - **Foundation:** convenções globais (error handling, logging, env config, TypeScript conventions, project structure).
   - **Domain:** padrões por camada (estrutura de endpoints Azure Functions, integração Azure AI Search, componentes React, testing patterns).
   - **Artifact:** receitas de geração (criar endpoint RAG, criar teste de integração, criar card React).

2. **Mapear, por skill:** nome, **descrição/frase-ativação** (o gatilho que um agente
   reconheceria), **quem cria** (papel), **quem consome** (papel + quais agentes) e
   **frequência de uso** estimada.

3. **Escrever o `SKILL.md` da Foundation mais importante (com Copilot).** Recomendado:
   `typescript-conventions.md` ou `error-handling.md` — a base que todas as outras referenciam.
   O arquivo deve conter:
   - **Contexto** (quando aplicar);
   - **Regras prescritivas** (DEVE / NÃO DEVE);
   - **Exemplos concretos** (blocos DO/DON'T com código TypeScript real);
   - **Anti-padrões** (erros que o Copilot realmente cometeria sem guidance).

---

## 5. Conceito necessário — Skills e a hierarquia Foundation → Domain → Artifact

> **Skills são artefatos estruturados (tipicamente `.md`) que encapsulam *como* gerar tipos
> específicos de output.** Funcionam como "memória de procedimento" do time, lida por agentes.

### A hierarquia (do geral para o específico)
| Nível | Escopo | Pergunta que responde | Exemplos no projeto |
|---|---|---|---|
| **Foundation** | Global, vale para todo código | "Quais convenções sempre se aplicam?" | TS strict, error handling, logging (pino), env config |
| **Domain** | Por camada/tecnologia | "Como estruturamos *este tipo* de componente?" | endpoint Azure Functions, integração AI Search, componente React, testes |
| **Artifact** | Receita de um output específico | "Passo a passo para gerar *este artefato*?" | criar endpoint RAG, criar teste de integração, criar card de resposta |

Camadas superiores **referenciam** as inferiores: um Artifact `create-rag-endpoint` reusa a
Domain `azure-functions-endpoint`, que por sua vez reusa a Foundation `error-handling`.
Assim a regra de erro é definida **uma vez**.

### Anatomia de um bom `SKILL.md`
1. **Frase-ativação / descrição** — quando o agente deve aplicar a skill.
2. **Contexto** — premissas e onde ela vale.
3. **Regras prescritivas** — DEVE / NÃO DEVE (imperativo, não descritivo).
4. **Exemplos DO/DON'T** — código real, lado a lado.
5. **Anti-padrões** — armadilhas concretas que o Copilot gera sem guidance.

### Exemplo de mapeamento criação/consumo
| Skill | Nível | Cria | Consome |
|---|---|---|---|
| `error-handling` | Foundation | Tech Lead | todos os devs + Copilot/Claude (toda geração de código) |
| `typescript-conventions` | Foundation | Tech Lead | todos os devs + agentes |
| `azure-functions-endpoint` | Domain | Dev Sênior | devs + Copilot (alta frequência) |
| `testing-patterns` | Domain | QA + Dev | QA, devs + Copilot |
| `react-components` | Domain | Dev (frontend) | devs do painel web + Copilot |
| `create-rag-endpoint` | Artifact | Dev Sênior | devs + Copilot (cada novo endpoint) |
| `create-integration-test` | Artifact | QA | QA + devs + Copilot |
| `sdd-spec-template` | Artifact | Product Specialist | PS + Tech Lead + Claude |

### Por que a Foundation é a "mais importante"
Ela é a única lida por **todas** as outras skills e por **toda** geração de código. Um erro
na Foundation se propaga para todos os artefatos; um acerto padroniza o projeto inteiro.
Por isso o exercício pede que ela seja escrita com exemplos concretos e anti-padrões reais.

---

## 6. Critérios de avaliação (do enunciado)

- [ ] A árvore de skills é **coerente** com o projeto (sem skills que ninguém usaria).
- [ ] A atribuição de **criação e consumo por papel** demonstra visão de time (não é só para devs).
- [ ] O `SKILL.md` Foundation é **concreto e prescritivo** (exemplos de código reais, não abstrações).
- [ ] Os **anti-padrões são úteis** (coisas que o Copilot realmente geraria de errado sem guidance).

## 7. Entregáveis

1. A **árvore de skills** (Foundation → Domain → Artifact) coerente com o projeto.
2. O **mapeamento** de criação/consumo por papel + frequência de uso.
3. O `SKILL.md` da **Foundation principal**, gerado com o Copilot, com DO/DON'T e anti-padrões.
