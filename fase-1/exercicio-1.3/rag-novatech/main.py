"""
Orquestrador principal do pipeline RAG NovaTech.

Integra os três módulos:
1. ingest.py — ingestão de documentos no ChromaDB
2. search.py — busca semântica por chunks relevantes
3. prompt_builder.py — montagem do prompt completo para o LLM

Uso interativo: permite testar queries e gerar prompts prontos para colar no Claude/ChatGPT.
"""
import os
import sys

from config import CHROMA_DIR, COLLECTION_NAME, DADOS_DIR


def check_prerequisites() -> bool:
    """Verifica se os documentos estão na pasta e o ChromaDB foi populado."""
    # Verificar pasta de dados
    if not os.path.exists(DADOS_DIR):
        print(f"❌ Pasta de dados não encontrada: {DADOS_DIR}")
        print("   Crie a pasta e copie os 5 documentos .md da NovaTech.")
        return False

    md_files = [f for f in os.listdir(DADOS_DIR) if f.endswith(".md")]
    if not md_files:
        print(f"❌ Nenhum arquivo .md encontrado em: {DADOS_DIR}")
        print("   Copie os documentos da NovaTech para a pasta dados/")
        return False

    # Verificar ChromaDB
    if not os.path.exists(CHROMA_DIR):
        print("⚠️  ChromaDB não encontrado. Execute a ingestão primeiro.")
        print("   Executando ingestão automaticamente...\n")
        from ingest import ingest
        ingest()

    return True


def interactive_mode():
    """Modo interativo: pergunta → busca → prompt completo."""
    from search import search_with_version_filter, print_results
    from prompt_builder import build_prompt, print_prompt

    print("\n" + "=" * 70)
    print("  🤖 ASSISTENTE RAG NOVATECH — Modo Interativo")
    print("=" * 70)
    print("\n  Comandos disponíveis:")
    print("    • Digite uma pergunta para gerar o prompt completo")
    print("    • 'tier GOLD|SILVER|STANDARD' — define o tier do cliente")
    print("    • 'topk N' — altera o número de chunks recuperados")
    print("    • 'ingest' — re-executa a ingestão de documentos")
    print("    • 'sair' — encerra o programa")
    print()

    client_tier = "DESCONHECIDO"
    top_k = 5

    while True:
        query = input("  📝 Pergunta: ").strip()

        if not query:
            continue
        if query.lower() in ("sair", "exit", "q"):
            print("\n  👋 Encerrando. Até logo!")
            break

        # Comandos especiais
        if query.lower().startswith("tier "):
            tier = query.split(" ", 1)[1].upper()
            if tier in ("GOLD", "SILVER", "STANDARD", "DESCONHECIDO"):
                client_tier = tier
                print(f"  ✅ Tier definido: {client_tier}\n")
            else:
                print("  ❌ Tier inválido. Use: GOLD, SILVER, STANDARD ou DESCONHECIDO\n")
            continue

        if query.lower().startswith("topk "):
            try:
                top_k = int(query.split(" ", 1)[1])
                print(f"  ✅ Top-K definido: {top_k}\n")
            except ValueError:
                print("  ❌ Valor inválido. Use um número inteiro.\n")
            continue

        if query.lower() == "ingest":
            from ingest import ingest
            ingest()
            continue

        # Pipeline RAG: busca → montagem de prompt
        print(f"\n  🔍 Buscando chunks relevantes (top-{top_k}, tier: {client_tier})...")
        results = search_with_version_filter(query, top_k=top_k)

        # Mostrar chunks recuperados
        print_results(results)

        # Montar e exibir prompt completo
        prompt = build_prompt(
            question=query,
            chunks=results,
            client_tier=client_tier,
        )
        print_prompt(prompt)

        # Opção de copiar para clipboard
        print("\n  💡 Copie o prompt acima e cole no Claude ou ChatGPT para obter a resposta.")
        print()


def batch_test():
    """Testa queries do mapa de cobertura do Anexo B para validação."""
    from search import search_with_version_filter

    test_queries = [
        ("Qual o prazo de devolução?", ["POL-001-A", "POL-001-B"]),
        ("Posso devolver carga perigosa?", ["POL-001-B"]),
        ("Qual o SLA do cliente Gold?", ["SLA-2024-B"]),
        ("Qual o SLA do cliente Platinum?", ["SLA-2024-A"]),
        ("Frete para 600kg para Manaus?", ["PROC-042v2-B", "PROC-042v2-A"]),
        ("Qual o multiplicador para o Sudeste?", ["PROC-042v2-B"]),
        ("O que acontece com carga danificada?", ["FAQ-38"]),
        ("Carga perigosa com frete expresso?", ["FAQ-32"]),
    ]

    print("\n" + "=" * 70)
    print("  🧪 TESTE DE VALIDAÇÃO — Mapa de Cobertura (Anexo B)")
    print("=" * 70)

    passed = 0
    total = len(test_queries)

    for query, expected_chunks in test_queries:
        results = search_with_version_filter(query, top_k=5)
        retrieved_ids = [r["id"] for r in results]

        # Verificar se pelo menos um chunk esperado está nos top-5
        found = any(expected in retrieved_ids for expected in expected_chunks)
        status = "✅" if found else "❌"
        if found:
            passed += 1

        print(f"\n  {status} Query: \"{query}\"")
        print(f"     Esperado: {expected_chunks}")
        print(f"     Recuperado (top-5): {retrieved_ids}")

    print(f"\n{'─' * 70}")
    print(f"  Resultado: {passed}/{total} queries com retrieval correto")
    print(f"{'─' * 70}")


def main():
    """Entry point principal."""
    if not check_prerequisites():
        sys.exit(1)

    # Verificar argumentos de linha de comando
    if len(sys.argv) > 1:
        if sys.argv[1] == "test":
            batch_test()
            return
        elif sys.argv[1] == "ingest":
            from ingest import ingest
            ingest()
            return

    # Modo interativo padrão
    interactive_mode()


if __name__ == "__main__":
    main()
