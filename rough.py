CREATE OR REPLACE TABLE apdrr_airr_foundry_dev_catalog.secured.embedding_historical_data AS
SELECT *,
  ai_embed('APDRR_embedding', Finding) AS Finding_Embedding,
  ai_embed('APDRR_embedding', Action) AS Action_Embedding
FROM apdrr_airr_foundry_dev_catalog.secured.prepare_historical_data;
