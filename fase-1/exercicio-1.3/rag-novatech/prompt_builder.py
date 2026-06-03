"""
Montagem do prompt completo para envio ao LLM.

Recebe os chunks recuperados e a pergunta do atendente, e monta o prompt
seguindo a estrutura definida no system-prompt-v1:

1. System prompt (estático)
2. Dados do cliente (dinâmico)
3. Contexto recuperado — chunks RAG ordenados por score (dinâmico)
4. Pergunta do atendente (dinâmico — no final para máxima atenção)

A ordem segue a recomendação da análise técnica para mitigar o efeito
"Lost in the Middle" (Liu et al., 2023).
"""
from config import SYSTEM_PROMPT


def build_prompt(
    question: str,
    chunks: list[dict],
    client_tier: str = "DESCONHECIDO",
    client_contract: str = "não informado",
) -> str:
    """
    Monta o prompt completo pronto para envio ao LLM.

    Args:
        question: Pergunta do atendente.
        chunks: Lista de chunks recuperados (output de search.search()).
        client_tier: Tier do cliente (GOLD, SILVER, STANDARD, DESCONHECIDO).
        client_contract: Número do contrato ou "não informado".

    Returns:
        String com o prompt completo formatado.
    """
    # 1. System prompt (estático)
    prompt_parts = [SYSTEM_PROMPT]

    # 2. Dados do cliente (dinâmico)
    prompt_parts.append(f"""
---
[DADOS DO CLIENTE]
Tier: {client_tier.upper()}
Número do contrato: {client_contract}
---""")

    # 3. Contexto recuperado (dinâmico — chunks ordenados por score)
    context_section = "\n[CONTEXTO RECUPERADO]\n"
    for chunk in chunks:
        chunk_id = chunk["id"]
        content = chunk["content"]
        score = chunk.get("score", 0)
        source = chunk.get("metadata", {}).get("source", "?")
        version_status = chunk.get("metadata", {}).get("version_status", "?")

        context_section += f"\n{chunk_id} [score: {score:.3f} | fonte: {source} | status: {version_status}]:\n"
        context_section += f'"{content}"\n'

    prompt_parts.append(context_section)

    # 4. Pergunta do atendente (no final — máxima atenção do modelo)
    prompt_parts.append(f"""---
[PERGUNTA DO ATENDENTE]
{question}
---""")

    return "\n".join(prompt_parts)


def build_prompt_for_clipboard(
    question: str,
    chunks: list[dict],
    client_tier: str = "DESCONHECIDO",
    client_contract: str = "não informado",
) -> str:
    """
    Versão do prompt formatada para colar em chat manual (Claude, ChatGPT, etc.).
    Inclui instruções de contexto e delimitadores claros.
    """
    prompt = build_prompt(question, chunks, client_tier, client_contract)

    header = (
        "# INSTRUÇÕES: Cole este prompt inteiro no chat com o LLM.\n"
        "# O conteúdo entre [SYSTEM] e [/SYSTEM] é o system prompt.\n"
        "# O restante é o contexto dinâmico da query.\n\n"
        "[SYSTEM]\n"
    )

    # Separar system prompt do restante
    parts = prompt.split("\n---\n[DADOS DO CLIENTE]")
    system_part = parts[0]
    dynamic_part = "[DADOS DO CLIENTE]" + parts[1] if len(parts) > 1 else ""

    return f"{header}{system_part}\n[/SYSTEM]\n\n---\n{dynamic_part}"


def print_prompt(prompt: str) -> None:
    """Imprime o prompt completo com formatação visual."""
    print("\n" + "=" * 70)
    print("  PROMPT COMPLETO PARA O LLM")
    print("=" * 70)
    print(prompt)
    print("\n" + "=" * 70)
    print(f"  Tamanho aproximado: ~{len(prompt.split())} palavras | ~{len(prompt)} caracteres")
    print("=" * 70)


if __name__ == "__main__":
    # Exemplo de montagem com chunks simulados
    sample_chunks = [
        {
            "id": "POL-001-AB",
            "content": "[POL-001 | Seção 3.1+3.2: Prazo geral e exceções]\nPRAZO: O cliente pode solicitar a devolução em até 7 dias úteis após o recebimento.\n\nEXCEÇÕES: Cargas perigosas classes 1-6 ANTT NÃO são elegíveis para devolução padrão.",
            "metadata": {"source": "POL-001", "version_status": "current"},
            "score": 0.92,
        },
        {
            "id": "SLA-2024-B",
            "content": "[SLA-2024 | Seção 2: SLAs para chamados gerais]\nGOLD: 1ª resposta → até 2h úteis | Resolução → até 24h úteis\nSILVER: 1ª resposta → até 4h úteis | Resolução → até 48h úteis",
            "metadata": {"source": "SLA-2024", "version_status": "current"},
            "score": 0.85,
        },
    ]

    prompt = build_prompt(
        question="O cliente quer devolver uma carga perigosa. O que respondo?",
        chunks=sample_chunks,
        client_tier="GOLD",
    )
    print_prompt(prompt)
