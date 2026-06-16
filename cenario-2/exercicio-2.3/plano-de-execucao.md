# Plano de Execução — Exercício 2.3 (Estratégia de skills)

> Execução posterior. Pré-requisito: Exercício 2.1 concluído (MCP ativo) para o agente
> enxergar `skills/`, `src/` e os padrões do projeto.

---

## Fase 0 — Preparação
- [ ] 0.1 Abrir o starter repo (Anexo D) com os MCP servers ativos.
- [ ] 0.2 Inspecionar `skills/foundation`, `skills/domain`, `skills/artifact` (arquivos vazios a preencher).
- [ ] 0.3 Revisar `AGENTS.md` e `src/shared/` (`logger.ts`, `errors.ts`, `config.ts`, `types.ts`) como fonte dos padrões reais.
- [ ] 0.4 Listar os artefatos repetitivos do projeto (endpoints RAG, testes de integração, cards React, docs, specs).

## Fase 1 — Definir a árvore de skills (com Claude)
- [ ] 1.1 Foundation: error-handling, typescript-conventions, project-structure, logging, env-config.
- [ ] 1.2 Domain: azure-functions-endpoint, azure-ai-search-integration, react-components, testing-patterns.
- [ ] 1.3 Artifact: create-rag-endpoint, create-integration-test, create-react-card, sdd-spec-template.
- [ ] 1.4 Validar coerência: toda skill mapeia a um artefato realmente recorrente (sem "skill órfã").
- [ ] 1.5 Definir as referências entre níveis (Artifact → Domain → Foundation).

## Fase 2 — Mapear criação/consumo (com Claude)
- [ ] 2.1 Para cada skill: nome + **frase-ativação** que o agente reconheceria.
- [ ] 2.2 Definir **quem cria** (papel) e **quem consome** (papel + agentes Copilot/Claude).
- [ ] 2.3 Estimar **frequência de uso** (alta/média/baixa).
- [ ] 2.4 Garantir visão de time: incluir skills consumidas por PS (sdd-spec-template) e QA (testing/integration-test).
- [ ] 2.5 Consolidar em tabela (entregável 2).

## Fase 3 — Escrever o SKILL.md da Foundation principal (com Copilot)
- [ ] 3.1 Escolher a Foundation base (recomendado: `error-handling.md` ou `typescript-conventions.md`).
- [ ] 3.2 Seção **Frase-ativação/Descrição**: quando o agente aplica a skill.
- [ ] 3.3 Seção **Contexto**: premissas e escopo de aplicação.
- [ ] 3.4 Seção **Regras prescritivas** (DEVE / NÃO DEVE), alinhadas ao AGENTS.md (pino, sem console.log, strict mode).
- [ ] 3.5 Seção **Exemplos DO/DON'T** com blocos de código TypeScript reais.
- [ ] 3.6 Seção **Anti-padrões**: erros que o Copilot geraria sem guidance (ex.: `catch (e) {}` silencioso, `any`, segredo hardcoded, log de payload com PII).
- [ ] 3.7 Salvar em `skills/foundation/<skill>.md` (entregável 3).

## Fase 4 — Validação
- [ ] 4.1 Teste prático: pedir ao Copilot para gerar um trecho de código **com** a skill carregada e **sem** ela; comparar aderência.
- [ ] 4.2 Conferir que as regras da Foundation não conflitam com o AGENTS.md.
- [ ] 4.3 Conferir os critérios de avaliação do enunciado.

## Fase 5 — Consolidação
- [ ] 5.1 Reunir entregáveis: árvore de skills, mapeamento criação/consumo, SKILL.md Foundation.
- [ ] 5.2 Commit com Conventional Commits (ex.: `docs(skills): add foundation error-handling skill and skills tree`).
