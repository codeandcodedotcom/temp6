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

    MAX_RESULT_CHARS = int(os.getenv("MAX_RESULT_CHARS", "100000"))

    # PATHS
    BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    QUESTIONNAIRE_PATH = os.path.join(BASE_DIR, "data", "questions.json")
    KPI_FILE_PATH = os.getenv("KPI_DATA_PATH", os.path.join(BASE_DIR, "data", "kpi_data.json"))
    DB_PATH = os.getenv("DB_PATH", os.path.join(BASE_DIR, "data", "database.db"))
    PROMPT_TEMPLATE_PATH = os.path.join(BASE_DIR, "data", "prompt_template.txt")
    OUTPUT_SCHEMA_PATH = os.path.join(BASE_DIR, "data", "output_template.json")

    # Error logging
    ERROR_LOG_FALLBACK_FILE = os.getenv("ERROR_LOG_FALLBACK_FILE")
    USE_DB_FOR_ERRORS = os.getenv("USE_DB_FOR_ERRORS", "False").lower() in ("true", "1", "yes")

    # Database
    DATABASE_URL = os.getenv("DATABASE_URL")



