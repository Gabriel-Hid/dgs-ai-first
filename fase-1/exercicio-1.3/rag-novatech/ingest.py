"""
Ingestão de documentos NovaTech no ChromaDB.

Etapas:
1. Lê os documentos .md da pasta dados/
2. Aplica estratégia de chunking semântico (por seção) com metadados
3. Gera embeddings via sentence-transformers (all-MiniLM-L6-v2)
4. Armazena no ChromaDB com metadados de autoridade e versão

Estratégia de Chunking (baseada nas análises técnicas da Fase 1):
- FAQ: 1 chunk por item (pergunta + resposta) — itens semanticamente independentes
- POL-001: chunking por seção com pair chunking das seções 3.1+3.2 (prazo + exceções)
- PROC-042-v1/v2: chunking por seção com metadado de versão obrigatório
- SLA-2024: chunking funcional por tipo de consulta (classificação, SLA geral, SLA crítico, etc.)

Justificativa geral: chunks pequenos (100-300 tokens) maximizam precisão de retrieval para
queries curtas de atendimento, minimizando o efeito "Lost in the Middle" (Liu et al., 2023).
Metadados de versão e autoridade permitem filtragem pós-retrieval.
"""
import os
import re
import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer

from config import (
    DADOS_DIR,
    CHROMA_DIR,
    EMBEDDING_MODEL,
    COLLECTION_NAME,
    DOCUMENT_METADATA,
)


def load_documents(dados_dir: str) -> dict[str, str]:
    """Lê todos os .md da pasta de dados e retorna dict {filename: conteúdo}."""
    documents = {}
    for filename in os.listdir(dados_dir):
        if filename.endswith(".md"):
            filepath = os.path.join(dados_dir, filename)
            with open(filepath, "r", encoding="utf-8") as f:
                documents[filename] = f.read()
    return documents


# =============================================================================
# ESTRATÉGIAS DE CHUNKING POR DOCUMENTO
# =============================================================================


def chunk_faq(content: str, filename: str) -> list[dict]:
    """
    FAQ: 1 chunk por item (pergunta + resposta).
    Cada item do FAQ é semanticamente independente — a query do atendente
    tende a ser semanticamente próxima da "Pergunta:" do FAQ.
    IDs usam o número real do item (ex: FAQ-03, FAQ-08).
    """
    chunks = []
    metadata_base = DOCUMENT_METADATA.get(filename, {})

    # Dividir por itens (### Item N — ...)
    items = re.findall(
        r'### Item (\d+)\s*[\u2014\-]\s*["\u201c](.+?)["\u201d]\s*\n(.*?)(?=### Item \d+|$)',
        content,
        re.DOTALL,
    )

    for item_num_str, title, body in items:
        item_num = int(item_num_str)
        body = body.strip()
        if not body:
            continue

        chunk_id = f"FAQ-{item_num:02d}"
        chunk_content = f"[FAQ-Atendimento | Item {item_num}: {title.strip()}]\n{body}"

        chunks.append({
            "id": chunk_id,
            "content": chunk_content,
            "metadata": {
                **metadata_base,
                "chunk_id": chunk_id,
                "section": f"Item {item_num}",
                "topic": title.strip().lower(),
            },
        })

    return chunks


def chunk_pol001(content: str, filename: str) -> list[dict]:
    """
    POL-001: Chunking semântico por seção.
    Seções 3.1 e 3.2 separadas (conforme Anexo B de referência).
    """
    chunks = []
    metadata_base = DOCUMENT_METADATA.get(filename, {})

    # Chunk A — Seção 3.1: Prazo geral
    match_31 = re.search(
        r"### 3\.1\. Prazo geral\s*(.*?)(?=### 3\.2\.)",
        content,
        re.DOTALL,
    )
    if match_31:
        chunks.append({
            "id": "POL-001-A",
            "content": (
                "[POL-001 | Seção 3.1: Prazo geral de devolução]\n"
                "Palavras-chave: prazo devolução, devolver mercadoria, dias úteis, prazo para devolver\n\n"
                f"{match_31.group(1).strip()}"
            ),
            "metadata": {
                **metadata_base,
                "chunk_id": "POL-001-A",
                "section": "3.1",
                "topic": "prazo-devolucao",
            },
        })

    # Chunk B — Seção 3.2: Exceções ao prazo geral
    match_32 = re.search(
        r"### 3\.2\. Exceções ao prazo geral\s*(.*?)(?=### 3\.3\.)",
        content,
        re.DOTALL,
    )
    if match_32:
        chunks.append({
            "id": "POL-001-B",
            "content": (
                "[POL-001 | Seção 3.2: Exceções — cargas não elegíveis para devolução]\n"
                "Palavras-chave: carga perigosa devolução, devolver carga perigosa, exceção devolução, "
                "não elegível, ANTT, posso devolver, categorias não aceitas\n\n"
                f"{match_32.group(1).strip()}"
            ),
            "metadata": {
                **metadata_base,
                "chunk_id": "POL-001-B",
                "section": "3.2",
                "topic": "excecoes-devolucao",
            },
        })

    # Chunk C — Seção 3.3: Procedimento de devolução
    match_33 = re.search(
        r"### 3\.3\. Procedimento de devolução\s*(.*?)(?=### 3\.[45]\.)",
        content,
        re.DOTALL,
    )
    if match_33:
        chunks.append({
            "id": "POL-001-C",
            "content": f"[POL-001 | Seção 3.3: Procedimento]\n{match_33.group(1).strip()}",
            "metadata": {
                **metadata_base,
                "chunk_id": "POL-001-C",
                "section": "3.3",
                "topic": "procedimento-devolucao",
            },
        })

    # Chunk D — Seção 3.5: Custos de devolução
    match_35 = re.search(
        r"### 3\.5\. Custos de devolução\s*(.*?)$",
        content,
        re.DOTALL,
    )
    if match_35:
        chunks.append({
            "id": "POL-001-D",
            "content": f"[POL-001 | Seção 3.5: Custos]\n{match_35.group(1).strip()}",
            "metadata": {
                **metadata_base,
                "chunk_id": "POL-001-D",
                "section": "3.5",
                "topic": "custos-devolucao",
            },
        })

    return chunks


def chunk_proc042(content: str, filename: str, version: str) -> list[dict]:
    """
    PROC-042 (v1 ou v2): Chunking por seção com metadado de versão obrigatório.
    Cada chunk inclui cabeçalho de status (CURRENT ou DEPRECATED).
    """
    chunks = []
    metadata_base = DOCUMENT_METADATA.get(filename, {})
    is_v2 = version == "v2"
    prefix = "PROC-042v2" if is_v2 else "PROC-042"
    status_label = "✅ VERSÃO ATUAL" if is_v2 else "⚠️ SUBSTITUÍDO por PROC-042-v2"

    # Chunk A — Fórmula + Fatores de peso
    match_formula = re.search(
        r"## 2\. Fórmula de cálculo\s*(.*?)(?=### 2\.1\.)",
        content,
        re.DOTALL,
    )
    if match_formula:
        header = f"[PROC-042 | Versão: {version} | Status: {status_label}]\n"
        chunks.append({
            "id": f"{prefix}-A",
            "content": header + f"[Seção 2: Fórmula de cálculo]\n{match_formula.group(1).strip()}",
            "metadata": {
                **metadata_base,
                "chunk_id": f"{prefix}-A",
                "section": "2",
                "topic": "formula-frete-especial",
            },
        })

    # Chunk B — Multiplicadores regionais
    match_mult = re.search(
        r"### 2\.1\. Multiplicadores regionais.*?\s*(.*?)(?=## 3\.)",
        content,
        re.DOTALL,
    )
    if match_mult:
        header = f"[PROC-042 | Versão: {version} | Status: {status_label}]\n"
        chunks.append({
            "id": f"{prefix}-B",
            "content": header + f"[Seção 2.1: Multiplicadores regionais]\n{match_mult.group(1).strip()}",
            "metadata": {
                **metadata_base,
                "chunk_id": f"{prefix}-B",
                "section": "2.1",
                "topic": "multiplicadores-regionais",
            },
        })

    # Chunk C — Prazo de entrega
    match_prazo = re.search(
        r"## 3\. Prazo de entrega.*?\s*(.*?)(?=## 4\.)",
        content,
        re.DOTALL,
    )
    if match_prazo:
        header = f"[PROC-042 | Versão: {version} | Status: {status_label}]\n"
        chunks.append({
            "id": f"{prefix}-C",
            "content": header + f"[Seção 3: Prazo de entrega]\n{match_prazo.group(1).strip()}",
            "metadata": {
                **metadata_base,
                "chunk_id": f"{prefix}-C",
                "section": "3",
                "topic": "prazo-frete-especial",
            },
        })

    # Chunk D — Condições especiais
    match_cond = re.search(
        r"## 4\. Condições especiais\s*(.*?)(?=## 5\.|$)",
        content,
        re.DOTALL,
    )
    if match_cond:
        header = f"[PROC-042 | Versão: {version} | Status: {status_label}]\n"
        chunks.append({
            "id": f"{prefix}-D",
            "content": header + f"[Seção 4: Condições especiais]\n{match_cond.group(1).strip()}",
            "metadata": {
                **metadata_base,
                "chunk_id": f"{prefix}-D",
                "section": "4",
                "topic": "condicoes-especiais-frete",
            },
        })

    # Chunk E — Disposições transitórias (apenas v2)
    if is_v2:
        match_trans = re.search(
            r"## 5\. Disposições transitórias\s*(.*?)$",
            content,
            re.DOTALL,
        )
        if match_trans:
            header = f"[PROC-042 | Versão: {version} | Status: {status_label}]\n"
            chunks.append({
                "id": f"{prefix}-E",
                "content": header + f"[Seção 5: Disposições transitórias]\n{match_trans.group(1).strip()}",
                "metadata": {
                    **metadata_base,
                    "chunk_id": f"{prefix}-E",
                    "section": "5",
                    "topic": "transicao-versoes",
                },
            })

    return chunks


def chunk_sla2024(content: str, filename: str) -> list[dict]:
    """
    SLA-2024: Chunking funcional por tipo de consulta.
    Serialização orientada por tier (não por tabela raw).
    """
    chunks = []
    metadata_base = DOCUMENT_METADATA.get(filename, {})

    # Chunk A — Classificação de clientes + nota Platinum inexistente
    match_class = re.search(
        r"## 1\. Classificação de clientes\s*(.*?)(?=## 2\.)",
        content,
        re.DOTALL,
    )
    if match_class:
        chunks.append({
            "id": "SLA-2024-A",
            "content": (
                "[SLA-2024 | Seção 1: Classificação de clientes]\n"
                f"{match_class.group(1).strip()}\n\n"
                "IMPORTANTE: NÃO existem outros tiers além de Gold, Silver e Standard. "
                "Não existe tier Platinum, Diamond ou Premium."
            ),
            "metadata": {
                **metadata_base,
                "chunk_id": "SLA-2024-A",
                "section": "1",
                "topic": "classificacao-tiers",
            },
        })

    # Chunk B — SLAs chamados gerais (serializado por tier)
    chunks.append({
        "id": "SLA-2024-B",
        "content": (
            "[SLA-2024 | Seção 2: SLAs para chamados gerais]\n"
            "GOLD:     1ª resposta → até 2h úteis | Resolução → até 24h úteis\n"
            "SILVER:   1ª resposta → até 4h úteis | Resolução → até 48h úteis\n"
            "STANDARD: 1ª resposta → até 8h úteis | Resolução → até 72h úteis\n\n"
            "Horário comercial: 08h-18h dias úteis. Relógio de SLA pausa fora desse horário para chamados gerais."
        ),
        "metadata": {
            **metadata_base,
            "chunk_id": "SLA-2024-B",
            "section": "2",
            "topic": "sla-chamados-gerais",
        },
    })

    # Chunk C — SLAs incidentes críticos (com nota Gold não pausa)
    chunks.append({
        "id": "SLA-2024-C",
        "content": (
            "[SLA-2024 | Seção 2: SLAs para incidentes críticos]\n"
            "GOLD:     1ª resposta → até 30min | Resolução → até 4h\n"
            "          ⚠️ GOLD: relógio NÃO pausa fora do horário comercial para incidentes críticos\n"
            "SILVER:   1ª resposta → até 1h | Resolução → até 8h\n"
            "STANDARD: 1ª resposta → até 2h | Resolução → até 24h"
        ),
        "metadata": {
            **metadata_base,
            "chunk_id": "SLA-2024-C",
            "section": "2",
            "topic": "sla-incidentes-criticos",
        },
    })

    # Chunk D — Definição de incidente crítico
    match_critico = re.search(
        r"## 3\. Definição de incidente crítico\s*(.*?)(?=## 4\.)",
        content,
        re.DOTALL,
    )
    if match_critico:
        chunks.append({
            "id": "SLA-2024-D",
            "content": f"[SLA-2024 | Seção 3: Definição de incidente crítico]\n{match_critico.group(1).strip()}",
            "metadata": {
                **metadata_base,
                "chunk_id": "SLA-2024-D",
                "section": "3",
                "topic": "definicao-incidente-critico",
            },
        })

    # Chunk E — Penalidades
    match_penal = re.search(
        r"## 4\. Penalidades por descumprimento\s*(.*?)(?=## 5\.)",
        content,
        re.DOTALL,
    )
    if match_penal:
        chunks.append({
            "id": "SLA-2024-E",
            "content": f"[SLA-2024 | Seção 4: Penalidades por descumprimento de SLA]\n{match_penal.group(1).strip()}",
            "metadata": {
                **metadata_base,
                "chunk_id": "SLA-2024-E",
                "section": "4",
                "topic": "penalidades-sla",
            },
        })

    return chunks


# =============================================================================
# DISPATCHER DE CHUNKING
# =============================================================================


def chunk_document(filename: str, content: str) -> list[dict]:
    """Aplica a estratégia de chunking adequada com base no nome do arquivo."""
    if "FAQ" in filename:
        return chunk_faq(content, filename)
    elif "POL-001" in filename:
        return chunk_pol001(content, filename)
    elif "PROC-042-v2" in filename or "v2" in filename:
        return chunk_proc042(content, filename, version="v2")
    elif "PROC-042" in filename:
        return chunk_proc042(content, filename, version="v1")
    elif "SLA-2024" in filename:
        return chunk_sla2024(content, filename)
    else:
        # Fallback: chunk único com o documento inteiro
        return [{
            "id": filename.replace(".md", ""),
            "content": content,
            "metadata": DOCUMENT_METADATA.get(filename, {"source": filename}),
        }]


# =============================================================================
# INGESTÃO NO CHROMADB
# =============================================================================


def ingest():
    """Pipeline de ingestão: lê documentos, chunka, gera embeddings e armazena."""
    print("=" * 60)
    print("  PIPELINE DE INGESTÃO — NovaTech RAG")
    print("=" * 60)

    # 1. Carregar documentos
    print(f"\n📂 Carregando documentos de: {DADOS_DIR}")
    documents = load_documents(DADOS_DIR)
    if not documents:
        print(f"❌ Nenhum documento .md encontrado em {DADOS_DIR}")
        print("   Copie os 5 documentos da NovaTech para a pasta dados/")
        return
    print(f"   Encontrados: {len(documents)} documentos")
    for name in sorted(documents.keys()):
        print(f"   • {name}")

    # 2. Chunking
    print("\n✂️  Aplicando estratégia de chunking...")
    all_chunks = []
    for filename, content in documents.items():
        chunks = chunk_document(filename, content)
        all_chunks.extend(chunks)
        print(f"   • {filename}: {len(chunks)} chunks gerados")

    print(f"\n   Total de chunks: {len(all_chunks)}")

    # 3. Gerar embeddings
    print(f"\n🧠 Carregando modelo de embedding: {EMBEDDING_MODEL}")
    model = SentenceTransformer(EMBEDDING_MODEL)
    print("   Gerando embeddings para todos os chunks...")
    texts = [chunk["content"] for chunk in all_chunks]
    embeddings = model.encode(texts, show_progress_bar=True).tolist()
    print(f"   Embeddings gerados: {len(embeddings)} vetores de dimensão {len(embeddings[0])}")

    # 4. Armazenar no ChromaDB
    print(f"\n💾 Armazenando no ChromaDB: {CHROMA_DIR}")
    client = chromadb.PersistentClient(path=CHROMA_DIR)

    # Deletar collection existente para recriar
    try:
        client.delete_collection(name=COLLECTION_NAME)
        print("   Collection anterior removida.")
    except Exception:
        pass

    collection = client.create_collection(
        name=COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"},  # Similaridade por cosseno
    )

    # Inserir chunks
    collection.add(
        ids=[chunk["id"] for chunk in all_chunks],
        embeddings=embeddings,
        documents=texts,
        metadatas=[chunk["metadata"] for chunk in all_chunks],
    )

    print(f"   ✅ {len(all_chunks)} chunks armazenados na collection '{COLLECTION_NAME}'")

    # 5. Resumo
    print("\n" + "=" * 60)
    print("  INGESTÃO CONCLUÍDA")
    print("=" * 60)
    print(f"\n  Chunks por documento:")
    from collections import Counter
    sources = Counter(chunk["metadata"].get("source", "?") for chunk in all_chunks)
    for source, count in sorted(sources.items()):
        print(f"    {source}: {count} chunks")
    print(f"\n  Total: {len(all_chunks)} chunks no ChromaDB")
    print(f"  Modelo: {EMBEDDING_MODEL}")
    print(f"  Distância: cosine similarity")


if __name__ == "__main__":
    ingest()
