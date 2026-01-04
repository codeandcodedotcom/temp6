from pyspark.sql import functions as F
from pyspark.sql.types import ArrayType, FloatType
from openai import OpenAI
import os

CATALOG = "apdrr_airr_foundry_dev_catalog"
SCHEMA = "secured"
SOURCE_TABLE = "prepare_historical_data"
TARGET_TABLE = "embedding_historical_data"
EMBEDDING_MODEL = "APDRR_embedding"

source_table_full = f"{CATALOG}.{SCHEMA}.{SOURCE_TABLE}"
target_table_full = f"{CATALOG}.{SCHEMA}.{TARGET_TABLE}"

df = spark.table(source_table_full)
print(f"Loaded {df.count()} rows")

host = "https://" + dbutils.notebook.entry_point.getDbutils().notebook().getContext().browserHostName().get()
token = dbutils.notebook.entry_point.getDbutils().notebook().getContext().apiToken().get()

client = OpenAI(
    api_key=token,
    base_url=f"{host}/serving-endpoints/{EMBEDDING_MODEL}/openai/v1"
)

def get_embedding(text):
    if text is None or str(text).strip() == "":
        return None
    try:
        res = client.embeddings.create(
            model=EMBEDDING_MODEL,
            input=str(text)
        )
        return res.data[0].embedding
    except Exception as e:
        print("Embedding error:", e)
        return None

get_embedding_udf = F.udf(get_embedding, ArrayType(FloatType()))

df_with_embeddings = (
    df
    .withColumn("Finding_Embedding", get_embedding_udf(F.col("Finding").cast("string")))
    .withColumn("Action_Embedding", get_embedding_udf(F.col("Action").cast("string")))
)

df_with_embeddings.select("Finding_Embedding","Action_Embedding").show(5, truncate=False)

df_with_embeddings.write.mode("overwrite").saveAsTable(target_table_full)
print("Embedding table created successfully")
