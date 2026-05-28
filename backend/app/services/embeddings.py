import httpx
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from app.core.config import settings


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    retry=retry_if_exception_type((httpx.HTTPError, httpx.TimeoutException)),
)
async def embed_text(text: str) -> list[float]:
    """
    Generate embeddings using Ollama's nomic-embed-text model.
    Uses the correct Ollama API endpoint: /api/embed
    """
    async with httpx.AsyncClient() as client:
        # Construct /api/embed from base URL (removing /v1 if present)
        base = settings.ollama_base_url.replace("/v1", "")
        resp = await client.post(
            f"{base}/api/embed",
            json={
                "model": "nomic-embed-text",
                "input": text,
            },
            timeout=30.0,
        )
        resp.raise_for_status()
        data = resp.json()
        return data["embeddings"][0]


async def embed_query(query: str) -> list[float]:
    """Generate embedding for a search query (JD text)."""
    return await embed_text(query)


async def embed_document(document: str) -> list[float]:
    """Generate embedding for a document to be indexed (resume)."""
    return await embed_text(document)