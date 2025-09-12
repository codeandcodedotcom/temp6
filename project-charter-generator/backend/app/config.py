import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    """
    Centralized configuration class. Reads values from environment variables.
    """

    # Azure OpenAI
    AZURE_OPENAI_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT")
    AZURE_OPENAI_KEY = os.getenv("AZURE_OPENAI_KEY")
    AZURE_API_VERSION = os.getenv("AZURE_API_VERSION")
    AZURE_EMBEDDING_DEPLOYMENT = os.getenv("AZURE_EMBEDDING_DEPLOYMENT")
    AZURE_CHAT_DEPLOYMENT = os.getenv("AZURE_CHAT_DEPLOYMENT")

    # Databricks
    DATABRICKS_HOST = os.getenv("DATABRICKS_HOST")
    DATABRICKS_TOKEN = os.getenv("DATABRICKS_TOKEN")
    DATABRICKS_JOB_ID = os.getenv("DATABRICKS_JOB_ID")

    try:
        MAX_TOKENS = int(os.getenv("MAX_TOKENS", "500"))
    except Exception:
        MAX_TOKENS = 500

    try:
        TEMPERATURE = float(os.getenv("TEMPERATURE", "0.3"))
    except Exception:
        TEMPERATURE = 0.3

    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key")
    TOP_K = int(os.getenv("TOP_K", "3"))

    DATABRICKS_TIMEOUT = float(os.getenv("DATABRICKS_TIMEOUT", "10"))
    DATABRICKS_MAX_RETRIES = int(os.getenv("DATABRICKS_MAX_RETRIES", "3"))
    DATABRICKS_RETRY_DELAY = float(os.getenv("DATABRICKS_RETRY_DELAY", "2"))

    AZURE_TIMEOUT = float(os.getenv("AZURE_TIMEOUT", "10"))
    AZURE_MAX_RETRIES = int(os.getenv("AZURE_MAX_RETRIES", "3"))
    AZURE_RETRY_DELAY = float(os.getenv("AZURE_RETRY_DELAY", "2"))

    ENTRA_TENANT_ID = os.getenv("ENTRA_TENANT_ID")
    ENTRA_CLIENT_ID = os.getenv("ENTRA_CLIENT_ID")
    ENTRA_AUTHORITY = f"https://login.microsoftonline.com/{ENTRA_TENANT_ID}/v2.0" if ENTRA_TENANT_ID else None
    ENTRA_JWKS_URL = f"https://login.microsoftonline.com/{ENTRA_TENANT_ID}/discovery/v2.0/keys" if ENTRA_TENANT_ID else None

    BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    QUESTIONNAIRE_PATH = os.path.join(BASE_DIR, "data", "questions.json")
    KPI_FILE_PATH = os.getenv("KPI_DATA_PATH", os.path.join(BASE_DIR, "data", "kpi_data.json"))

    DB_PATH = os.getenv("DB_PATH", os.path.join(BASE_DIR, "data", "database.db"))

    MAX_RESULT_CHARS = int(os.getenv("MAX_RESULT_CHARS", "200000"))


    PROMPT_TEMPLATE = """You are a project-charter generator assistant.

    Given:
    1) User answers (as JSON array of question objects): {answers_json}
    2) Context documents (as a list of short text snippets): {context_text}

    Task:
    Produce a single valid JSON object (and ONLY the JSON object) that exactly matches this schema and nothing else:

    {
    "project_title": "string",
    "domain": "string",
    "project_description": "string",
    "objectives": ["string", "..."],
    "project_scope": "string",
    "timeline": [
        {
        "phase": "string",
        "duration": "string",
        "tasks": ["string", "..."]
        }
    ],
    "budget": {
        "total_budget": "string or number",
        "currency": "string (optional)",
        "breakdown": [
        {"category": "string", "percentage": number}
        ]
    },
    "risks": [
        {"title":"string","impact":"Low|Medium|High","mitigation":"string"}
    ],
    "team": {
        {"role":"string","count": integer, "responsibilities": ["string", "..."]}
    },
    "recommended_pm_count": integer,
    "success_criteria": ["string", "..."],
    "resources_required": ["string", "..."],
    "tools_and_technologies": ["string", "..."],
    "recommendation": "string",
    "rationale": "string (explain briefly how score was derived)"
    }

    Instructions:
    - Use the user answers and context documents to populate the fields.
    - Use the scoring summary below to guide complexity-sensitive recommendations.
    - If a particular field cannot be inferred, use a sensible default (empty string, empty array, or 0 for numbers).
    - Do NOT include any text before or after the JSON. Respond with EXACTLY one JSON object matching the schema above.
    - Ensure date fields (if present) use ISO format YYYY-MM-DD.

    Scoring summary:
    {scoring_summary}

    User answers (JSON):
    {answers_json}

    Context (short snippets):
    {context_text}
    """
