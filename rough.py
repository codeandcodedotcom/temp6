raw = (managed_by or "").strip().lower()

if raw.startswith("self"):
    band_key = "self_managed"
elif raw.startswith("project lead"):
    band_key = "project_lead"
elif raw.startswith("project manager"):
    band_key = "project_manager"
elif raw.startswith("team of pm"):
    band_key = "team_of_PM_professionals"
else:
    logger.warning("Unknown managed_by value: %r", managed_by)
    continue
