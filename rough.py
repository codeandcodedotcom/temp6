from pyspark.sql import functions as F
from pyspark.sql.types import ArrayType, FloatType
import pandas as pd
import requests, json

CATALOG = "apdrr_airr_foundry_dev_catalog"
SCHEMA = "secured"
SOURCE_TABLE = "prepare_historical_data"
TARGET_TABLE = "embedding_historical_data"
EMBEDDING_MODEL = "APDRR_embedding"

# Load data
df = spark.table(f"{CATALOG}.{SCHEMA}.{SOURCE_TABLE}")

# Get token & host (driver safe)
TOKEN = dbutils.notebook.entry_point.getDbutils().notebook().getContext().apiToken().get()
HOST  = dbutils.notebook.entry_point.getDbutils().notebook().getContext().apiUrl().get().replace("https://", "")

URL = f"https://{HOST}/serving-endpoints/{EMBEDDING_MODEL}/invocations"
HEADERS = {
    "Authorization": f"Bearer {TOKEN}",
    "Content-Type": "application/json"
}

def embed_batch(texts):
    payload = { "input": texts }
    r = requests.post(URL, headers=HEADERS, json=payload, timeout=60)
    r.raise_for_status()
    return [x["embedding"] for x in r.json()["data"]]

def pandas_embed(pdf: pd.DataFrame) -> pd.DataFrame:
    texts_f = pdf["Finding"].fillna("").astype(str).tolist()
    texts_a = pdf["Action"].fillna("").astype(str).tolist()

    pdf["Finding_Embedding"] = embed_batch(texts_f)
    pdf["Action_Embedding"]  = embed_batch(texts_a)
    return pdf

result = df.mapInPandas(
    pandas_embed,
    schema=df.schema
        .add("Finding_Embedding", ArrayType(FloatType()))
        .add("Action_Embedding",  ArrayType(FloatType()))
)

result.write.mode("overwrite").saveAsTable(f"{CATALOG}.{SCHEMA}.{TARGET_TABLE}")
print("DONE — APDRR_embedding vectors generated.")
