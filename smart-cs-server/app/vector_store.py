"""Vector Store — FAISS-based semantic search for FAQ knowledge base.

Uses DashScope (or any OpenAI-compatible) Embedding API to generate text
embeddings, then performs cosine similarity search via FAISS.

Graceful degradation: if EMBEDDING_API_KEY is empty or the API call fails,
the module stays uninitialized and the caller falls back to keyword search.
"""

import logging
from typing import Optional

import numpy as np

from app.config import EMBEDDING_API_KEY, EMBEDDING_BASE_URL, EMBEDDING_MODEL

logger = logging.getLogger(__name__)

# Module-level state
_index = None              # faiss.IndexFlatIP
_documents: list = []      # [{id, question, answer, intent, keywords}, ...]
_initialized: bool = False


def is_initialized() -> bool:
    """Check if the vector store is ready for semantic search."""
    return _initialized


async def init_vector_store(faq_data: list[dict]) -> None:
    """Build FAISS index from FAQ data using embedding API.

    Called once during app startup. If EMBEDDING_API_KEY is missing or the
    API call fails, the store remains uninitialized (graceful degradation).

    Args:
        faq_data: List of FAQ dicts from knowledge_base.FAQ_DATA.
    """
    global _index, _documents, _initialized

    if not EMBEDDING_API_KEY or EMBEDDING_API_KEY == "your-dashscope-api-key":
        logger.warning(
            "EMBEDDING_API_KEY not configured — vector store disabled, "
            "falling back to keyword search. Set EMBEDDING_API_KEY in .env to enable RAG."
        )
        return

    try:
        import faiss
        from langchain_openai import OpenAIEmbeddings

        # Build embedding client (OpenAI-compatible, pointed at DashScope)
        embeddings = OpenAIEmbeddings(
            api_key=EMBEDDING_API_KEY,
            base_url=EMBEDDING_BASE_URL,
            model=EMBEDDING_MODEL,
        )

        # Prepare texts to embed: combine question + answer for richer semantics
        texts = []
        for faq in faq_data:
            combined = f"{faq['question']} {faq['answer']}"
            texts.append(combined)

        # Generate embeddings (synchronous call wrapped in async context)
        logger.info(f"Generating embeddings for {len(texts)} FAQ entries via {EMBEDDING_MODEL}...")
        vectors = embeddings.embed_documents(texts)

        # Convert to numpy and normalize (L2 normalize for cosine similarity via inner product)
        vectors_np = np.array(vectors, dtype=np.float32)
        faiss.normalize_L2(vectors_np)

        # Build FAISS index (Inner Product = cosine similarity after normalization)
        dimension = vectors_np.shape[1]
        _index = faiss.IndexFlatIP(dimension)
        _index.add(vectors_np)

        # Store document metadata for retrieval
        _documents = [
            {
                "id": faq["id"],
                "question": faq["question"],
                "answer": faq["answer"],
                "intent": faq["intent"],
                "keywords": faq.get("keywords", []),
            }
            for faq in faq_data
        ]

        _initialized = True
        logger.info(
            f"Vector store initialized: {len(_documents)} documents, "
            f"dimension={dimension}, index={type(_index).__name__}"
        )

    except ImportError:
        logger.error(
            "faiss-cpu or numpy not installed — vector store disabled. "
            "Run: pip install faiss-cpu numpy"
        )
    except Exception as e:
        logger.error(f"Vector store initialization failed: {e}")
        _index = None
        _documents = []
        _initialized = False


async def search_similar(query: str, top_k: int = 3) -> list[dict]:
    """Semantic similarity search against the FAQ knowledge base.

    Args:
        query: User's question or search query.
        top_k: Maximum number of results to return.

    Returns:
        List of dicts: [{question, answer, intent, similarity_score, id}, ...]
        Ordered by descending similarity. Returns empty list if not initialized.
    """
    if not _initialized or _index is None:
        return []

    try:
        from langchain_openai import OpenAIEmbeddings

        embeddings = OpenAIEmbeddings(
            api_key=EMBEDDING_API_KEY,
            base_url=EMBEDDING_BASE_URL,
            model=EMBEDDING_MODEL,
        )

        # Embed the query
        query_vector = embeddings.embed_query(query)
        query_np = np.array([query_vector], dtype=np.float32)

        # Normalize for cosine similarity
        import faiss
        faiss.normalize_L2(query_np)

        # Search FAISS index
        k = min(top_k, len(_documents))
        scores, indices = _index.search(query_np, k)

        # Build results
        results = []
        for score, idx in zip(scores[0], indices[0]):
            if idx < 0 or idx >= len(_documents):
                continue
            doc = _documents[idx]
            results.append({
                "id": doc["id"],
                "question": doc["question"],
                "answer": doc["answer"],
                "intent": doc["intent"],
                "similarity_score": float(score),  # cosine similarity, 0~1
            })

        return results

    except Exception as e:
        logger.error(f"Vector search failed: {e}")
        return []
