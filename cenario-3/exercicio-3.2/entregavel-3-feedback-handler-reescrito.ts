// feedback/handler.ts — reescrito com GitHub Copilot
// Localização no projeto: src/functions/feedback/handler.ts
//
// Correções aplicadas em relação à versão gerada pelo Copilot:
//   R-1: body validado com Zod (schema FeedbackBodySchema)
//   R-2: logging via pino (logger) em vez de console.log
//   R-3: attendantEmail removido — dado pessoal não coletado nem persistido
//   R-4: import estático de CosmosClient no topo do arquivo
//   R-5: COSMOS_CONNECTION_STRING via config.ts com requireEnv() — falha no startup se ausente
//   R-6: try/catch no Cosmos DB com AppError + log estruturado
//   R-7: requestId (UUID v4) gerado no início do handler
//   R-8: status 201 (Created) + jsonBody para retorno consistente com Azure Functions v4

import { app, HttpRequest, HttpResponseInit } from '@azure/functions';
import { CosmosClient } from '@azure/cosmos';
import { randomUUID } from 'node:crypto';
import { z } from 'zod';

import { logger } from '../../shared/logger.js';
import { AppError, ValidationError, toErrorResponse } from '../../shared/errors.js';
import { getConfig } from '../../shared/config.js';

// ─── Schema de validação do body ─────────────────────────────────────────────
//
// Campos coletados para análise de qualidade de respostas:
//   queryId  — identificador da consulta que está sendo avaliada
//   rating   — nota do atendente (1 = muito ruim, 5 = excelente)
//   comment  — observação livre, opcional
//
// Campo REMOVIDO em relação à versão original: attendantEmail
//   Motivo: dado pessoal (PII) — não deve ser coletado nem persistido.
//   Rastreabilidade é obtida via queryId, que referencia a sessão da consulta.

const FeedbackBodySchema = z
  .object({
    queryId: z.string().min(1, 'queryId é obrigatório'),
    rating: z
      .number({ invalid_type_error: 'rating deve ser um número' })
      .int('rating deve ser inteiro')
      .min(1, 'rating mínimo é 1')
      .max(5, 'rating máximo é 5'),
    comment: z.string().max(1000, 'comment não pode exceder 1000 caracteres').optional(),
  })
  .strict(); // rejeita campos extras

type FeedbackBody = z.infer<typeof FeedbackBodySchema>;

// ─── Handler ──────────────────────────────────────────────────────────────────

export async function feedbackHandler(
  request: HttpRequest,
): Promise<HttpResponseInit> {
  const requestId = randomUUID();

  // ── 1. Validação de input com Zod ─────────────────────────────────────────
  let rawBody: unknown;
  try {
    rawBody = await request.json();
  } catch {
    logger.warn({ requestId }, 'Body da requisição não é JSON válido');
    const err = new ValidationError('Body da requisição deve ser JSON válido');
    return { status: 400, jsonBody: toErrorResponse(err) };
  }

  const parseResult = FeedbackBodySchema.safeParse(rawBody);
  if (!parseResult.success) {
    const message = parseResult.error.errors
      .map((issue) => `${issue.path.join('.')}: ${issue.message}`)
      .join('; ');
    logger.warn({ requestId, validationErrors: parseResult.error.flatten().fieldErrors }, 'Input inválido');
    const err = new ValidationError(message);
    return { status: 400, jsonBody: toErrorResponse(err) };
  }

  const body: FeedbackBody = parseResult.data;

  // ── 2. Log estruturado — apenas metadados, sem PII nem comment ────────────
  //
  // Campos logados:   requestId, queryId, rating
  // Campos OMITIDOS:  comment (conteúdo livre — pode ter PII do cliente)
  //                   attendantEmail (removido do schema — não coletado)
  logger.info(
    {
      requestId,
      queryId: body.queryId,
      rating: body.rating,
    },
    'Feedback recebido',
  );

  // ── 3. Persistência no Cosmos DB ──────────────────────────────────────────
  try {
    const config = getConfig();
    const client = new CosmosClient(config.cosmos.connectionString); // requireEnv() internamente
    const container = client.database('novatech').container('feedbacks');

    const feedbackDocument = {
      id: randomUUID(),            // ID único do documento Cosmos DB
      queryId: body.queryId,
      rating: body.rating,
      comment: body.comment,       // opcional — null/undefined se não enviado
      timestamp: new Date().toISOString(),
      // attendantEmail: removido — dado pessoal, não coletado
    };

    await container.items.create(feedbackDocument);

    logger.info({ requestId, queryId: body.queryId }, 'Feedback persistido com sucesso');
  } catch (err: unknown) {
    if (err instanceof AppError) {
      logger.error({ requestId, code: err.code, err }, 'Erro de domínio ao persistir feedback');
      return { status: err.httpStatus, jsonBody: toErrorResponse(err) };
    }
    logger.error({ requestId, err }, 'Erro inesperado ao persistir feedback no Cosmos DB');
    return { status: 500, jsonBody: toErrorResponse(err) };
  }

  // ── 4. Resposta — 201 Created ─────────────────────────────────────────────
  return {
    status: 201,                  // Created — recurso foi criado no Cosmos DB
    jsonBody: { success: true },  // jsonBody (não body) para resposta JSON consistente
  };
}

// ─── Registro do endpoint ─────────────────────────────────────────────────────

app.http('feedback', {
  methods: ['POST'],
  authLevel: 'function',
  handler: feedbackHandler,
});
