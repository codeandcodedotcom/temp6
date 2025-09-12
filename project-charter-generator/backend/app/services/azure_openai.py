import os
import time
from typing import Any, Callable, Optional, Sequence
import httpx
from openai import AzureOpenAI
from app.config import Config
from app.utils.logger import get_logger

logger = get_logger(__name__)

try:
    REQUEST_TIMEOUT = float(getattr(Config, "AZURE_TIMEOUT", 10) or 10)
except Exception:
    REQUEST_TIMEOUT = 10.0

try:
    MAX_RETRIES = int(getattr(Config, "AZURE_MAX_RETRIES", 3) or 3)
except Exception:
    MAX_RETRIES = 3

try:
    RETRY_DELAY = float(getattr(Config, "AZURE_RETRY_DELAY", 2) or 2)
except Exception:
    RETRY_DELAY = 2.0

if not getattr(Config, "AZURE_OPENAI_ENDPOINT", None) or not getattr(Config, "AZURE_OPENAI_KEY", None):
    logger.error("Azure OpenAI endpoint/key not configured in Config (AZURE_OPENAI_ENDPOINT/AZURE_OPENAI_KEY)")

http_client = httpx.Client(timeout=REQUEST_TIMEOUT)

client = AzureOpenAI(
    azure_endpoint=getattr(Config, "AZURE_OPENAI_ENDPOINT", None),
    api_key=getattr(Config, "AZURE_OPENAI_KEY", None),
    api_version=getattr(Config, "AZURE_API_VERSION", None),
    http_client=http_client
)

EMBEDDING_DEPLOYMENT = getattr(Config, "AZURE_EMBEDDING_DEPLOYMENT", None)
CHAT_DEPLOYMENT = getattr(Config, "AZURE_CHAT_DEPLOYMENT", None)


def _with_retry(func, *args, **kwargs):
    """
    Run func with retries. Raises the final exception if all retries fail.
    """
    func_name = getattr(func, "__name__", repr(func))
    last_exc = None
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            logger.info(f"Azure API call {func_name} attempt={attempt}/{MAX_RETRIES}")
            return func(*args, **kwargs)
        except Exception as e:
            last_exc = e
            logger.warning(f"Azure API call {func_name} failed on attempt {attempt}: {e}", exc_info=True)
            if attempt < MAX_RETRIES:
                time.sleep(RETRY_DELAY)
            else:
                logger.error(f"Azure API call {func_name} failed after {MAX_RETRIES} attempts")
                raise


def embed_text(text: str) -> Sequence[float]:
    """
    Create embeddings for input text using Azure OpenAI embedding model.
    Returns:
        embedding as a list of floats
    """
    if not EMBEDDING_DEPLOYMENT:
        raise RuntimeError("Embedding deployment not configured (EMBEDDING_DEPLOYMENT)")

    response = _with_retry(
        client.embeddings.create,
        model=EMBEDDING_DEPLOYMENT,
        input=text,
    )

    try:
        embedding = response.data[0].embedding
        if not isinstance(embedding, (list, tuple)):
            raise ValueError("Invalid embedding type returned from Azure")
    except Exception as e:
        logger.exception("Unexpected embedding response shape")
        raise RuntimeError(f"Failed to extract embedding from Azure response: {e}")

    logger.info(f"Generated embedding (len={len(embedding)}) for text length={len(text)}")
    return embedding


def generate_answer(prompt: str, max_tokens: Optional[int] = None, temperature: Optional[float] = None) -> str:
    """
    Generate text using Azure OpenAI chat model.

    Args:
      prompt: string prompt
      max_tokens: override from Config if provided
      temperature: override if provided

    Returns:
      The model's textual response
    """
    if not CHAT_DEPLOYMENT:
        raise RuntimeError("Chat deployment not configured (CHAT_DEPLOYMENT)")

    max_tokens = max_tokens if max_tokens is not None else getattr(Config, "MAX_TOKENS", 500)
    temperature = temperature if temperature is not None else getattr(Config, "TEMPERATURE", 0.3)

    response = _with_retry(
        client.chat.completions.create,
        model=CHAT_DEPLOYMENT,
        messages=[{"role": "user", "content": prompt}],
        max_tokens=max_tokens,
        temperature=temperature
    )

    try:
        answer = response.choices[0].message.content
        if not isinstance(answer, str):
            raise ValueError("Model did not return string content")
    except Exception as e:
        logger.exception("Unexpected chat completion response shape")
        raise RuntimeError(f"Failed to extract chat message from Azure response: {e}")

    logger.info(f"LLM response generated successfully (length={len(answer)})")
    return answer
