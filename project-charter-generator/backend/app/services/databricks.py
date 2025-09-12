import requests
import json
from app.config import Config
from app.utils.logger import get_logger
import time

logger = get_logger(__name__)

REQUEST_TIMEOUT = int(Config.DATABRICKS_TIMEOUT or 10)  
MAX_RETRIES = int(Config.DATABRICKS_MAX_RETRIES or 3)  
RETRY_DELAY = int(Config.DATABRICKS_RETRY_DELAY or 2)  


def _post_with_retry(url, headers, payload):
    """
    POST with retries and timeout.
    """
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            logger.info(f"POST {url} attempt={attempt}/{MAX_RETRIES}")
            response = requests.post(
                url,
                headers=headers,
                json=payload,
                timeout=REQUEST_TIMEOUT
            )
            response.raise_for_status()
            return response.json()
        except (requests.Timeout, requests.ConnectionError) as e:
            logger.warning(
                f"Databricks request timeout/connection error on attempt {attempt}: {e}"
            )
        except requests.HTTPError as e:
            if 500 <= response.status_code < 600:
                logger.warning(
                    f"Databricks server error {response.status_code} on attempt {attempt}"
                )
            else:
                logger.error(
                    f"Databricks returned HTTP {response.status_code}: {response.text}"
                )
                raise
        except Exception as e:
            logger.error(f"Unexpected error on attempt {attempt}: {e}", exc_info=True)
            raise

        if attempt < MAX_RETRIES:
            time.sleep(RETRY_DELAY)

    raise RuntimeError("Databricks request failed after max retries")


def run_job(job_id: str, params: dict = None):
    """
    Trigger a Databricks job via REST API.
    Returns the raw response JSON.
    """
    if not Config.DATABRICKS_TOKEN:
        raise RuntimeError("DATABRICKS_TOKEN is not configured")

    url = f"{Config.DATABRICKS_HOST}/api/2.1/jobs/run-now"
    headers = {"Authorization": f"Bearer {Config.DATABRICKS_TOKEN}"}
    payload = {"job_id": job_id}

    if params:
        payload["notebook_params"] = params

    logger.info(f"Triggering Databricks job_id={job_id} with params={params}")
    return _post_with_retry(url, headers, payload)



def retrieve_context(embedding: list, top_k: int = 3):
    """
    Calls a Databricks job that runs semantic search on stored vectors.
    Returns retrieved documents/context.
    """
    try:
        params = {
            "embedding": json.dumps(embedding),
            "top_k": str(top_k)
        }
        job_id = Config.DATABRICKS_JOB_ID

        logger.info(f"Retrieving context from Databricks (job_id={job_id}, top_k={top_k})")
        result = run_job(job_id, params)

        docs = result.get("documents", [])
        if not docs:
            logger.error(f"Documents is not present in the provided output from databicks")
            raise RuntimeError("Invalid response: missing 'documents'")

        if docs is None:
            logger.error(f"Databricks response missing 'documents' key: {result}")
            raise RuntimeError("Invalid Databricks response: missing 'documents'")
            
        logger.info(f"Retrieved {len(docs)} documents from Databricks")
        return docs
    except Exception as e:
        logger.error(f"Context retrieval from Databricks failed: {e}", exc_info=True)
        raise
