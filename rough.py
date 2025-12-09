from datetime import datetime, timedelta  # add timedelta to your existing import

# ...

def _fy_quarter(dt: datetime) -> str:
    """
    Map a datetime to a financial-year quarter.

    FY starts in April:
    Q1: Apr–Jun, Q2: Jul–Sep, Q3: Oct–Dec, Q4: Jan–Mar.
    """
    m = dt.month
    if 4 <= m <= 6:
        return "Q1"
    elif 7 <= m <= 9:
        return "Q2"
    elif 10 <= m <= 12:
        return "Q3"
    else:
        return "Q4"



----


async def get_returning_users(
    session: AsyncSession,
    days: int | None = None,
) -> List[Dict[str, Any]]:
    """
    Compute 'new_user' vs 'returning_user' counts per quarter.

    Logic (per user):
    - First ever project they create => counted as `new_user` in that quarter.
    - Every subsequent project => counted as `returning_user` in the quarter
      where that project was created (can be same or later quarter).

    `days` is optional; if provided, we only consider projects created in the
    last `days` days.
    """
    logger.info("KPI: computing new vs returning users (days=%s)", days)

    stmt = select(Project.user_id, Project.created_at)

    if days is not None:
        cutoff = datetime.utcnow() - timedelta(days=int(days))
        stmt = stmt.where(Project.created_at >= cutoff)

    result = await session.execute(stmt)
    rows = result.all()

    # If no data, return empty quarters
    if not rows:
        return [
            {"Quarter": q, "new_user": 0, "returning_user": 0}
            for q in ("Q1", "Q2", "Q3", "Q4")
        ]

    # Collect all project creation dates per user
    user_projects: Dict[Any, List[datetime]] = {}
    for user_id, created_at in rows:
        if not user_id or not created_at:
            continue
        user_projects.setdefault(user_id, []).append(created_at)

    # Per-quarter sets of users so we don't double-count
    quarter_stats = {
        "Q1": {"new_user": set(), "returning_user": set()},
        "Q2": {"new_user": set(), "returning_user": set()},
        "Q3": {"new_user": set(), "returning_user": set()},
        "Q4": {"new_user": set(), "returning_user": set()},
    }

    for user_id, dates in user_projects.items():
        if not dates:
            continue

        dates_sorted = sorted(dates)

        # First ever project => "new_user" in that quarter
        first_quarter = _fy_quarter(dates_sorted[0])
        quarter_stats[first_quarter]["new_user"].add(user_id)

        # Every later project => "returning_user" in that quarter
        for dt in dates_sorted[1:]:
            q = _fy_quarter(dt)
            quarter_stats[q]["returning_user"].add(user_id)

    # Shape result to match existing JSON + Pydantic alias:
    #   {"Quarter": "Q1", "new_user": X, "returning_user": Y}
    data = [
        {
            "Quarter": q,
            "new_user": len(quarter_stats[q]["new_user"]),
            "returning_user": len(quarter_stats[q]["returning_user"]),
        }
        for q in ("Q1", "Q2", "Q3", "Q4")
    ]

    logger.info("KPI: returning-users result = %s", data)
    return data

-----

@router.get("/kpi/returning-users", response_model=List[ReturningUserEntry])
async def returning_users(
    session: AsyncSession = Depends(get_db_session),
) -> List[ReturningUserEntry]:
    """
    Returns the count of new user vs returning user per quarter.
    """
    try:
        data = await kpi_service.get_returning_users(session=session)
        return data
    except Exception:
        logger.exception("Failed to fetch new vs returning users data.")
        raise HTTPException(
            status_code=500,
            detail="Failed to fetch new vs returning users data.",
        )
