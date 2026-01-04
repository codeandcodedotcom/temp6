def get_embedding(text):
    if text is None or str(text).strip() == "":
        return None
    try:
        from openai import OpenAI
        import os
        
        host = "https://" + dbutils.notebook.entry_point.getDbutils().notebook().getContext().browserHostName().get()
        token = dbutils.notebook.entry_point.getDbutils().notebook().getContext().apiToken().get()

        client = OpenAI(
            api_key=token,
            base_url=f"{host}/serving-endpoints/{EMBEDDING_MODEL}/openai/v1"
        )

        res = client.embeddings.create(
            model=EMBEDDING_MODEL,
            input=str(text)
        )
        return res.data[0].embedding
    except Exception as e:
        print("Embedding error:", e)
        return None
