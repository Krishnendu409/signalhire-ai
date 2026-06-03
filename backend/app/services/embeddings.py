import asyncio
import logging
from functools import lru_cache

import httpx
from google import genai
from google.api_core.exceptions import GoogleAPICallError
from google.genai import types
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from app.core.config import settings

logger = logging.getLogger(__name__)
_embedding_warmed = False
_embedding_warmup_lock = asyncio.Lock()


@lru_cache(maxsize=1)
def _get_gemini_client() -> genai.Client:
    if not settings.gemini_api_key:
        raise RuntimeError("GEMINI_API_KEY is not configured")
    return genai.Client(api_key=settings.gemini_api_key)


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    retry=retry_if_exception_type((httpx.HTTPError, httpx.TimeoutException)),
)
async def _embed_with_ollama(text: str) -> list[float]:
    """Generate embeddings using Ollama."""
    async with httpx.AsyncClient() as client:
        base = settings.ollama_base_url.replace("/v1", "")
        resp = await client.post(
            f"{base}/api/embed",
            json={
                "model": settings.ollama_embedding_model,
                "input": text,
            },
            timeout=30.0,
        )
        resp.raise_for_status()
        data = resp.json()
        return data["embeddings"][0]


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    retry=retry_if_exception_type((GoogleAPICallError, ConnectionError, TimeoutError)),
)
async def _embed_with_gemini(text: str) -> list[float]:
    """Generate embeddings using Gemini."""
    response = await asyncio.to_thread(
        _get_gemini_client().models.embed_content,
        model=settings.gemini_embedding_model,
        contents=text,
        config=types.EmbedContentConfig(output_dimensionality=settings.embedding_dimension),
    )
    if not response.embeddings:
        raise RuntimeError("Gemini embedding response was empty")
    return list(response.embeddings[0].values)


async def embed_text(text: str) -> list[float]:
    """
    Generate embeddings with provider fallback.

    Tries the provider set by EMBEDDING_PROVIDER first ("ollama" or "gemini"),
    then falls back to the other provider if the primary call fails. If both
    providers fail, the final exception is raised to the caller.
    """
    primary = settings.embedding_provider.strip().lower()
    if primary == "gemini":
        try:
            return await _embed_with_gemini(text)
        except Exception as gemini_error:
            logger.warning(
                "Gemini embedding failed (text_len=%s), falling back to Ollama: %s",
                len(text),
                gemini_error,
            )
            return await _embed_with_ollama(text)

    try:
        return await _embed_with_ollama(text)
    except Exception as ollama_error:
        logger.warning(
            "Ollama embedding failed (text_len=%s), falling back to Gemini: %s",
            len(text),
            ollama_error,
        )
        return await _embed_with_gemini(text)


async def embed_query(query: str) -> list[float]:
    """Generate embedding for a search query (JD text)."""
    return await embed_text(query)


async def embed_document(document: str) -> list[float]:
    """Generate embedding for a document to be indexed (resume)."""
    return await embed_text(document)


async def warmup_embeddings() -> None:
    """Warm up embedding model(s) so first retrieval request is not cold."""
    global _embedding_warmed
    if _embedding_warmed:
        return
    async with _embedding_warmup_lock:
        if _embedding_warmed:
            return
        try:
            await embed_text("Senior backend engineer with Python, distributed systems, and cloud architecture experience.")
            _embedding_warmed = True
        except Exception as error:
            logger.warning("Embedding warmup skipped: %s", error)