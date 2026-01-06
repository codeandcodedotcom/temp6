- script: |
    export ENV_NAME="dev"
    export SKIP_AZURE_AUTH=true
    python generate_swagger.py
  workingDirectory: $(Build.SourcesDirectory)/src
  displayName: "Generate Swagger JSON"


if os.environ.get("SKIP_AZURE_AUTH", "").lower() in ("1", "true", "yes"):
    os.environ["DATABRICKS_TOKEN"] = "dummy-token"
    os.environ["DATABRICKS_HOST"] = "https://dummy"
    return
