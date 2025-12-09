# ----- Helper: month -> fiscal quarter -----
def _get_quarter(month: int) -> str:
    """
    Map a calendar month (1-12) to *fiscal* quarters:
    Q1: Apr-Jun, Q2: Jul-Sep, Q3: Oct-Dec, Q4: Jan-Mar.
    """
    if month in (4, 5, 6):
        return "Quarter 1"
    if month in (7, 8, 9):
        return "Quarter 2"
    if month in (10, 11, 12):
        return "Quarter 3"
    # Jan, Feb, Mar
    return "Quarter 4"


async def get_department_charters(session: AsyncSession) -> List[Dict[str, Any]]:
    """
    Charter counts per department per fiscal quarter,
    broken down by PM band.
    """
    logger.info("Fetching department charter counts from projects table...")

    stmt = (
        select(
            Project.department,
            Project.managed_by,
            extract("month", Project.created_at).label("month"),
        )
        .where(
            Project.department.isnot(None),
            Project.created_at.isnot(None),
            Project.managed_by.isnot(None),
        )
    )

    result = await session.execute(stmt)
    rows = result.all()

    # data[dept][quarter_label] = { band -> count }
    data: Dict[str, Dict[str, Dict[str, int]]] = {}

    for dept, managed_by, month in rows:
        if dept is None or month is None:
            continue

        # Initialise quarters for this department once
        if dept not in data:
            data[dept] = {
                "Quarter 1": {
                    "self_managed": 0,
                    "team_lead": 0,
                    "project_manager": 0,
                    "team_of_PM_professionals": 0,
                },
                "Quarter 2": {
                    "self_managed": 0,
                    "team_lead": 0,
                    "project_manager": 0,
                    "team_of_PM_professionals": 0,
                },
                "Quarter 3": {
                    "self_managed": 0,
                    "team_lead": 0,
                    "project_manager": 0,
                    "team_of_PM_professionals": 0,
                },
                "Quarter 4": {
                    "self_managed": 0,
                    "team_lead": 0,
                    "project_manager": 0,
                    "team_of_PM_professionals": 0,
                },
            }

        quarter = _get_quarter(int(month))

        # Normalise managed_by text
        raw = (managed_by or "").strip().lower()
        band_key: str | None = None

        if raw.startswith("self"):
            band_key = "self_managed"
        elif raw.startswith("project lead"):
            band_key = "team_lead"
        elif raw.startswith("project manager"):
            band_key = "project_manager"
        elif raw.startswith("team of pm"):
            band_key = "team_of_PM_professionals"
        else:
            logger.warning("Unknown managed_by value for KPI: %r", managed_by)
            continue

        data[dept][quarter][band_key] += 1

    # Convert to list for API output
    final_output: List[Dict[str, Any]] = [
        {
            "department": dept,
            "quarters": quarters,
        }
        for dept, quarters in sorted(data.items())
    ]

    logger.info(
        "KPI: generated department charter summary (%d departments)",
        len(final_output),
    )
    return final_output
