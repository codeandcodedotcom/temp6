def set_databricks_env(cfg=None):
    """
    Sets BOTH primary and CDP Databricks environments
    """

    if os.getenv("SKIP_AZURE_AUTH") or os.getenv("SKIP_DBX_AUTH_ON_STARTUP"):
        os.environ["DATABRICKS_TOKEN"] = "dummy-token"
        os.environ["DATABRICKS_CDP_TOKEN"] = "dummy-token"
        return

    if cfg is None:
        from hydra import compose, initialize
        with initialize(config_path="../config", version_base=None):
            cfg = compose(config_name="config")

    credential = DefaultAzureCredential()

    # --------------------------
    # PRIMARY WORKSPACE
    # --------------------------
    primary_host = os.getenv("DATABRICKS_HOST") or cfg.databricks.databricks_host
    primary_resource = cfg.databricks.resource

    primary_token = credential.get_token(primary_resource).token

    os.environ["DATABRICKS_HOST"] = primary_host
    os.environ["DATABRICKS_TOKEN"] = primary_token

    logger.info(f"Primary DBX set: {primary_host}")

    # --------------------------
    # CDP WORKSPACE (NEW)
    # --------------------------
    cdp_host = cfg.databricks.cdp.host
    cdp_resource = cfg.databricks.cdp.resource

    cdp_token = credential.get_token(cdp_resource).token

    os.environ["DATABRICKS_CDP_HOST"] = cdp_host
    os.environ["DATABRICKS_CDP_TOKEN"] = cdp_token

    logger.info(f"CDP DBX set: {cdp_host}")
