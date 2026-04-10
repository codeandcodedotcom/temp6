import json
import os
import requests

def _load_json_safe(path):
    try:
        # ✅ Detect Databricks volume path
        if path.startswith("/Volumes"):
            host = os.getenv("DATABRICKS_CDP_HOST")
            token = os.getenv("DATABRICKS_CDP_TOKEN")

            url = f"{host}/api/2.0/fs/files{path}"

            headers = {
                "Authorization": f"Bearer {token}"
            }

            response = requests.get(url, headers=headers)

            if not response.ok:
                print(f"Databricks read failed: {response.text}")
                return {}

            return json.loads(response.text)

        # ✅ Default local behavior
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)

    except Exception as e:
        print(f"Error loading JSON: {e}")
        return {}
