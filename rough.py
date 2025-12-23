raw = (managed_by or "").lower()

if "self" in raw:
    band_key = "self_managed"
elif "it project lead" in raw or "project lead" in raw:
    band_key = "team_lead"
elif "project manager" in raw:
    band_key = "project_manager"
elif "team of pm" in raw:
    band_key = "team_of_PM_professionals"
else:
    logger.warning("Unknown managed_by value for KPI: %s", managed_by)
    continue
