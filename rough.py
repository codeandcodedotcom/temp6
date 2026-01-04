from pyspark.sql import functions as F
from pyspark.sql.types import ArrayType, FloatType
from openai import OpenAI

# =========================
# CONFIG
# =========================

CATALOG = "apdrr_airr_foundry_dev_catalog"
SCHEMA = "secured"
SOURCE_TABLE = "prepare_historical_data"
TARGET_TABLE = "embedding_historical_data"
EMBEDDING_MODEL = "APDRR_embedding"

# =========================
# LOAD DATA
# =========================

source_table_full = f"{CATALOG}.{SCHEMA}.{SOURCE_TABLE}"
target_table_full = f"{CATALOG}.{SCHEMA}.{TARGET_TABLE}"

df = spark.table(source_table_full)
print("Rows:", df.count())

# =========================
# CAPTURE TOKEN & HOST (DRIVER)
# =========================

HOST = "https://" + dbutils.notebook.entry_point.getDbutils().notebook().getContext().browserHostName().get()
TOKEN = dbutils.notebook.entry_point.getDbutils().notebook().getContext().apiToken().get()

bc_host = spark.sparkContext.broadcast(HOST)
bc_token = spark.sparkContext.broadcast(TOKEN)

# =========================
# EMBEDDING FUNCTION (EXECUTOR SAFE)
# =========================

def get_embedding(text):
    if text is None or str(text).strip() == "":
        return None
    try:
        from openai import OpenAI
        
        client = OpenAI(
            api_key=bc_token.value,
            base_url=f"{bc_host.value}/serving-endpoints/{EMBEDDING_MODEL}/openai/v1"
        )

        res = client.embeddings.create(
            model=EMBEDDING_MODEL,
            input=str(text)
        )
        return res.data[0].embedding
    except:
        return None

# =========================
# REGISTER UDF
# =========================

get_embedding_udf = F.udf(get_embedding, ArrayType(FloatType()))

# =========================
# GENERATE EMBEDDINGS
# =========================

df_with_embeddings = (
    df
    .withColumn("Finding_Embedding", get_embedding_udf(F.col("Finding").cast("string")))
    .withColumn("Action_Embedding", get_embedding_udf(F.col("Action").cast("string")))
)

# =========================
# PREVIEW
# =========================

df_with_embeddings.select("Finding_Embedding", "Action_Embedding").show(5, truncate=False)

# =========================
# SAVE TO DELTA
# =========================

df_with_embeddings.write.mode("overwrite").saveAsTable(target_table_full)

print("✅ Embedding table created successfully:", target_table_full)
