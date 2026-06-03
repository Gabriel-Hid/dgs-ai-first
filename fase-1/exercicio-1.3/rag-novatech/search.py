"""
Módulo de busca semântica no ChromaDB.

Recebe uma pergunta, gera o embedding, busca os N chunks mais similares
e retorna os chunks com score de similaridade e metadados.
"""
import chromadb
from sentence_transformers import SentenceTransformer

from config import CHROMA_DIR, COLLECTION_NAME, EMBEDDING_MODEL, TOP_K


# Cache do modelo para evitar recarregamento em múltiplas queries
_model = None


def get_model() -> SentenceTransformer:
    """Carrega o modelo de embedding (singleton)."""
    global _model
    if _model is None:
        _model = SentenceTransformer(EMBEDDING_MODEL)
    return _model


def search(
    query: str,
    top_k: int = TOP_K,
    filter_metadata: dict | None = None,
) -> list[dict]:
    """
    Busca semântica: recebe uma pergunta, retorna os chunks mais similares.

    Args:
        query: Pergunta do atendente em linguagem natural.
        top_k: Número de chunks a retornar (default: config.TOP_K).
        filter_metadata: Filtro opcional de metadados ChromaDB (ex: {"version_status": "current"}).

    Returns:
        Lista de dicts com keys: id, content, metadata, score (distância cosseno).
        Ordenados por relevância decrescente (menor distância = mais similar).
    """
    # Gerar embedding da query
    model = get_model()
    query_embedding = model.encode(query).tolist()

    # Conectar ao ChromaDB
    client = chromadb.PersistentClient(path=CHROMA_DIR)
    collection = client.get_collection(name=COLLECTION_NAME)

    # Montar parâmetros de busca
    query_params = {
        "query_embeddings": [query_embedding],
        "n_results": top_k,
        "include": ["documents", "metadatas", "distances"],
    }

    # Aplicar filtro de metadados se fornecido
    if filter_metadata:
        query_params["where"] = filter_metadata

    # Executar busca
    results = collection.query(**query_params)

    # Formatar resultados
    chunks = []
    for i in range(len(results["ids"][0])):
        distance = results["distances"][0][i]
        # Converter distância cosseno para score de similaridade (1 - distance)
        similarity_score = 1 - distance

        chunks.append({
            "id": results["ids"][0][i],
            "content": results["documents"][0][i],
            "metadata": results["metadatas"][0][i],
            "distance": distance,
            "score": similarity_score,
        })

    return chunks


def search_with_version_filter(
    query: str,
    top_k: int = TOP_K,
    prefer_current: bool = True,
) -> list[dict]:
    """
    Busca com filtro inteligente de versão.

    Para chamados atuais (>= 01/12/2023), filtra documentos deprecated.
    Implementa a recomendação das análises técnicas de priorizar PROC-042-v2.

    Args:
        query: Pergunta do atendente.
        top_k: Número de resultados.
        prefer_current: Se True, filtra chunks com version_status="deprecated".

    Returns:
        Lista de chunks ordenados por relevância.
    """
    if prefer_current:
        return search(
            query=query,
            top_k=top_k,
            filter_metadata={"version_status": "current"},
        )
    return search(query=query, top_k=top_k)


def print_results(results: list[dict]) -> None:
    """Imprime os resultados de busca de forma legível."""
    print(f"\n{'─' * 60}")
    print(f"  {len(results)} chunks recuperados")
    print(f"{'─' * 60}")

    for i, chunk in enumerate(results, 1):
        source = chunk["metadata"].get("source", "?")
        section = chunk["metadata"].get("section", "?")
        score = chunk["score"]
        authority = chunk["metadata"].get("authority", "?")
        version_status = chunk["metadata"].get("version_status", "?")

        print(f"\n  [{i}] {chunk['id']} (score: {score:.4f})")
        print(f"      Fonte: {source} | Seção: {section}")
        print(f"      Autoridade: {authority} | Status: {version_status}")
        print(f"      Conteúdo (primeiros 200 chars):")
        preview = chunk["content"][:200].replace("\n", " ")
        print(f"      \"{preview}...\"")

    print(f"\n{'─' * 60}")


if __name__ == "__main__":
    # Teste interativo de busca
    print("=" * 60)
    print("  BUSCA SEMÂNTICA — NovaTech RAG")
    print("=" * 60)
    print("\n  Digite uma pergunta para buscar (ou 'sair' para encerrar):\n")

    while True:
        query = input("  🔍 Pergunta: ").strip()
        if query.lower() in ("sair", "exit", "q"):
            break
        if not query:
            continue

        # Busca com filtro de versão (preferindo documentos atuais)
        results = search_with_version_filter(query)
        print_results(results)
