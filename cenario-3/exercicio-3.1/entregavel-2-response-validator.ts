// response-validator.ts
// Camada de Harness — Guardrails Determinísticos
// Localização no projeto: src/services/response-validator.ts
//
// Propósito: validar a resposta do LLM antes de entregá-la ao atendente.
// Opera APÓS o LLM gerar a resposta, ANTES de enviar ao usuário.
//
// Dois níveis de proteção:
//   1. Structured output: valida o schema Zod (campos obrigatórios, tipos)
//   2. Guardrails de negócio: regras determinísticas sobre o conteúdo
//
// Em qualquer falha → loga o motivo + retorna SAFE_DEFAULT_RESPONSE
// (nunca lança exceção para o caller — o validator é o safety net final)

import { logger } from '../shared/logger.js';
import { AppError } from '../shared/errors.js';
import {
  AssistantResponseSchema,
  SAFE_DEFAULT_RESPONSE,
  type AssistantResponse,
} from '../shared/types.js';

// ─── Tipos de resultado ───────────────────────────────────────────────────────

export type ValidatorSuccess = {
  valid: true;
  data: AssistantResponse;
};

export type ValidatorFailure = {
  valid: false;
  reason: GuardrailViolation;
  safeResponse: AssistantResponse;
};

export type ValidatorResult = ValidatorSuccess | ValidatorFailure;

export type GuardrailViolation =
  | 'SCHEMA_INVALID'          // Resposta não corresponde ao structured output schema
  | 'GUARDRAIL_SOURCE_MISSING' // source_document ausente ou vazio (GR-1)
  | 'GUARDRAIL_DANGEROUS_GOODS'; // Afirma que devolução de carga perigosa é possível (GR-2)

// ─── Regex do Guardrail 2 — carga perigosa + devolução afirmativa ─────────────
//
// Estratégia: detectar COMBINAÇÃO de dois padrões no mesmo texto
//   Padrão A (carga perigosa): variações de "carga perigosa" e "cargas perigosas"
//   Padrão B (devolução afirmativa): variações de "devolução", "devolver", "devolvida", etc.
//
// Só bloqueia quando AMBOS estão presentes E o texto NÃO contém negativas explícitas.
// Negativas: "não", "nao" (sem acento), "impossível", "impossivel", "proibido",
//            "vedado", "não é possível", "não pode", "não permite"
//
// Exemplos que BLOQUEIAM (ambos os padrões, sem negativa):
//   "Sim, cargas perigosas podem ser devolvidas..."
//   "A devolução de carga perigosa é permitida..."
//   "Pode devolver a carga perigosa..."
//
// Exemplos que NÃO bloqueiam (negativa presente):
//   "Não é possível devolver carga perigosa..."
//   "A devolução de cargas perigosas é proibida..."
//   "Cargas perigosas não podem ser devolvidas..."

const DANGEROUS_GOODS_PATTERN = /cargas?\s+perigosas?/i;

const RETURN_AFFIRMATIVE_PATTERN = /devolu[çc][aã]o|devolver|devolvid[ao]s?|devolv[eê]/i;

const NEGATION_PATTERN =
  /\bn[aã]o\b|impossível|impossivel|proibid[ao]|vedad[ao]|n[aã]o\s+(é\s+)?possível|n[aã]o\s+pode|n[aã]o\s+permit/i;

// ─── Função principal ─────────────────────────────────────────────────────────

/**
 * Valida a resposta bruta do LLM contra o schema de structured output
 * e aplica guardrails determinísticos de negócio.
 *
 * @param rawResponse - Objeto recebido do LLM (pode ser malformado)
 * @param requestId   - UUID da requisição para correlação de logs
 * @returns ValidatorResult — success com data tipada, ou failure com safe default
 */
export function validateAssistantResponse(
  rawResponse: unknown,
  requestId: string,
): ValidatorResult {
  // ── Nível 1: Structured Output — validação do schema Zod ──────────────────
  const parseResult = AssistantResponseSchema.safeParse(rawResponse);

  if (!parseResult.success) {
    const zodErrors = parseResult.error.flatten().fieldErrors;
    logger.warn(
      {
        requestId,
        reason: 'SCHEMA_INVALID' satisfies GuardrailViolation,
        // Loga os campos com erro, mas NÃO o valor recebido (pode conter PII)
        invalidFields: Object.keys(zodErrors),
        zodErrors,
      },
      'Structured output inválido — resposta do LLM rejeitada',
    );

    return {
      valid: false,
      reason: 'SCHEMA_INVALID',
      safeResponse: SAFE_DEFAULT_RESPONSE,
    };
  }

  const response = parseResult.data;

  // ── Nível 2: Guardrail 1 — source_document não pode ser vazio ─────────────
  // O schema já exige .min(1), mas esta verificação explícita garante que
  // valores como "   " (apenas espaços) também são rejeitados.
  if (!response.source_document.trim()) {
    logger.warn(
      {
        requestId,
        reason: 'GUARDRAIL_SOURCE_MISSING' satisfies GuardrailViolation,
        confidence_score: response.confidence_score,
        // NÃO loga response.answer — pode conter PII ou conteúdo sensível
      },
      'GR-1 violado: source_document vazio após trim — resposta bloqueada',
    );

    return {
      valid: false,
      reason: 'GUARDRAIL_SOURCE_MISSING',
      safeResponse: SAFE_DEFAULT_RESPONSE,
    };
  }

  // ── Nível 2: Guardrail 2 — carga perigosa + devolução afirmativa ──────────
  // Bloqueia respostas que afirmem ser possível devolver carga perigosa.
  // Fundamentado na POL-001, seção 3.2: cargas ANTT classes 1-6 são inelegíveis.
  const hasDangerousGoods = DANGEROUS_GOODS_PATTERN.test(response.answer);
  const hasReturnAffirmative = RETURN_AFFIRMATIVE_PATTERN.test(response.answer);
  const hasNegation = NEGATION_PATTERN.test(response.answer);

  if (hasDangerousGoods && hasReturnAffirmative && !hasNegation) {
    logger.warn(
      {
        requestId,
        reason: 'GUARDRAIL_DANGEROUS_GOODS' satisfies GuardrailViolation,
        confidence_score: response.confidence_score,
        source_document: response.source_document,
        // Loga apenas a fonte e a confiança — não loga o texto da resposta
        // para evitar armazenar conteúdo problemático em logs persistentes
      },
      'GR-2 violado: resposta afirma devolução de carga perigosa — bloqueada por POL-001 seção 3.2',
    );

    return {
      valid: false,
      reason: 'GUARDRAIL_DANGEROUS_GOODS',
      safeResponse: SAFE_DEFAULT_RESPONSE,
    };
  }

  // ── Todos os níveis passaram ───────────────────────────────────────────────
  logger.debug(
    {
      requestId,
      source_document: response.source_document,
      confidence_score: response.confidence_score,
    },
    'Resposta validada com sucesso — todos os guardrails passaram',
  );

  return { valid: true, data: response };
}
