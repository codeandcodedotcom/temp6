from flask import Blueprint, request, jsonify
from app.services import azure_openai, databricks
from app.utils.logger import get_logger
from app.config import Config
import json

MAX_EMBED_CHARS = int(getattr(Config, "EMBED_MAX_CHARS", 20000))

logger = get_logger(__name__)

bp = Blueprint("test", __name__)

@bp.route("/test_embedding", methods=["POST"])
def test_embedding():
    """
    Test endpoint: create embedding for given text.
    Request: { "text": "your input" }
    Response: { "embedding_length": 1536, "sample_vector": [...] }
    """
    data = request.json
    text = data.get("text", "")

    if not text:
        logger.warning("No text provided for embedding request")
        return jsonify({"error": "No text provided"}), 400

    if len(text) > MAX_EMBED_CHARS:
        logger.info(f"Truncating input from {len(text)} to {MAX_EMBED_CHARS} chars for embedding test")
        text = text[:MAX_EMBED_CHARS]

    try:
        embedding = azure_openai.embed_text(text)
        logger.info(f"Embedding generated for input length={len(text)}")
        return jsonify({
            "embedding_length": len(embedding),
            "sample_vector": embedding[:5]
        })
    except Exception:
        logger.exception("Embedding test endpoint failed")
        return jsonify({"error": "Embedding service failed"}), 500



@bp.route("/test_llm", methods=["POST"])
def test_llm():
    """
    Test endpoint: generate response using Azure LLM.
    Request: { "prompt": "your question" }
    Response: { "answer": "LLM output here" }
    """
    data = request.json
    prompt = data.get("prompt", "")

    if not prompt:
        logger.warning("No prompt provided for LLM test request")
        return jsonify({"error": "No prompt provided"}), 400

    try:
        answer = azure_openai.generate_answer(prompt)
        logger.info(f"LLM response generated for prompt length={len(prompt)}")
        return jsonify({"answer": answer})
    except Exception as e:
        logger.error(f"LLM test endpoint failed: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500



@bp.route("/test_retriever", methods=["POST"])
def test_retriever():
    """
    Test endpoint: call Databricks retriever with a dummy embedding.
    Request: { "text": "your input" }
    Response: { "documents": [...] }
    """
    data = request.json
    text = data.get("text", "")

    if not text:
        logger.warning("No text provided for retriever test request")
        return jsonify({"error": "No text provided"}), 400

    try:
        # Step 1: Get embedding from Azure
        embedding = azure_openai.embed_text(text)

        # Step 2: Retrieve context from Databricks
        docs = databricks.retrieve_context(embedding)
        try:
            json.dumps(docs)
        except Exception:
            docs = [dict(d) if hasattr(d, "asDict") else d for d in docs]


        logger.info(f"Retriever returned {len(docs)} documents for input length={len(text)}")
        return jsonify({"documents": docs})
    except Exception as e:
        logger.error(f"Retriever test endpoint failed: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500
