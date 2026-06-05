from qdrant_client import AsyncQdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
from app.core.config import settings

client = AsyncQdrantClient(host=settings.qdrant_host, port=settings.qdrant_port)


async def init_qdrant():
    """Create collections if they don't exist. Fail silently if Qdrant is offline."""
    try:
        if not await client.collection_exists("candidates"):
            await client.create_collection(
                collection_name="candidates",
                vectors_config=VectorParams(size=settings.embedding_dimension, distance=Distance.COSINE),
            )

        if not await client.collection_exists("jobs"):
            await client.create_collection(
                collection_name="jobs",
                vectors_config=VectorParams(size=settings.embedding_dimension, distance=Distance.COSINE),
            )
        print("✅ Qdrant collections initialized.")
    except Exception as e:
        print(f"⚠️ Qdrant not available: {e}. Semantic search will be disabled.")


async def index_candidate(candidate_id: str, embedding: list[float], payload: dict):
    """Upsert a candidate's primary embedding into Qdrant."""
    await client.upsert(
        collection_name="candidates",
        points=[
            PointStruct(
                id=candidate_id,
                vector=embedding,
                payload=payload,
            )
        ],
    )


async def index_job(job_id: str, embedding: list[float], payload: dict):
    """Upsert a job description embedding into Qdrant."""
    await client.upsert(
        collection_name="jobs",
        points=[
            PointStruct(
                id=job_id,
                vector=embedding,
                payload=payload,
            )
        ],
    )


async def search_candidates(query_embedding: list[float], top_k: int = 50) -> list:
    """Semantic search over candidate embeddings. Returns list of ScoredPoint."""
    results = await client.search(
        collection_name="candidates",
        query_vector=query_embedding,
        limit=top_k,
    )
    return results


async def delete_candidate(candidate_id: str):
    """Remove a candidate from the vector index."""
    await client.delete(
        collection_name="candidates",
        points_selector=[candidate_id],
    )