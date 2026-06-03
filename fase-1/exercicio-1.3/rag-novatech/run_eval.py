"""Script de avaliação: executa 5 queries e gera outputs detalhados."""
from search import search_with_version_filter
from prompt_builder import build_prompt

queries = [
    "Qual o prazo de devolução?",
    "Posso devolver carga perigosa?",
    "Qual o SLA do cliente Gold?",
    "Qual o SLA do cliente Platinum?",
    "Frete para 600kg para Manaus?",
]

gabarito = {
    "Qual o prazo de devolução?": ["POL-001-A", "POL-001-B"],
    "Posso devolver carga perigosa?": ["POL-001-B"],
    "Qual o SLA do cliente Gold?": ["SLA-2024-B"],
    "Qual o SLA do cliente Platinum?": ["SLA-2024-A"],
    "Frete para 600kg para Manaus?": ["PROC-042v2-B", "PROC-042v2-A"],
}

for q in queries:
    print("=" * 70)
    print(f"QUERY: {q}")
    print("=" * 70)
    
    results = search_with_version_filter(q, top_k=5)
    expected = gabarito[q]
    retrieved_ids = [r["id"] for r in results]
    
    # Verificar acerto
    found = [e for e in expected if e in retrieved_ids]
    missed = [e for e in expected if e not in retrieved_ids]
    
    print(f"\n  Esperado:    {expected}")
    print(f"  Recuperado:  {retrieved_ids}")
    print(f"  Acertos:     {found}")
    print(f"  Faltando:    {missed}")
    print(f"\n  Detalhamento dos chunks recuperados:")
    
    for i, r in enumerate(results, 1):
        mark = "✅" if r["id"] in expected else "⚠️"
        print(f"    {mark} {i}. [{r['id']}]")
        print(f"       Score: {r['score']:.4f} | Source: {r['metadata'].get('source','?')} | Section: {r['metadata'].get('section','?')}")
        print(f"       Preview: {r['content'][:150].replace(chr(10), ' ')}")
        print()
    
    # Gerar prompt
    prompt = build_prompt(question=q, chunks=results, client_tier="GOLD")
    print(f"  Prompt gerado: {len(prompt)} caracteres")
    print("-" * 70)
    print()

# Gerar prompt completo para cada query (para colar no Claude)
print("\n\n" + "#" * 70)
print("# PROMPTS COMPLETOS PARA COLAR NO CLAUDE")
print("#" * 70)

for q in queries:
    results = search_with_version_filter(q, top_k=5)
    prompt = build_prompt(question=q, chunks=results, client_tier="GOLD")
    print(f"\n{'='*70}")
    print(f"### PROMPT PARA: {q}")
    print(f"{'='*70}")
    print(prompt)
    print(f"\n{'='*70}\n")
