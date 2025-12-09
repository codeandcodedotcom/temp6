

async def get_charters_per_month(session: AsyncSession) -> List[Dict[str, Any]]:
    """
    Return list of rows like:
    {
        "month": "January",
        "self_managed": 15,
        "project_lead": 7,
        "project_manager": 5,
        "team_of_PM_professionals": 28,
    }
    computed from the projects table.
    """

    # Truncate created_at to month for grouping
    month_expr = func.date_trunc("month", Project.created_at).label("month")

    # Normalise managed_by text once (lowercase + trim)
    managed_norm = func.trim(func.lower(Project.managed_by))

    stmt = (
        select(
            month_expr,
            # Self managed
            func.sum(
                case(
                    (managed_norm.like("self managed%"), 1),
                    else_=0,
                )
            ).label("self_managed"),
            # Project lead
            func.sum(
                case(
                    (managed_norm.like("project lead%"), 1),
                    else_=0,
                )
            ).label("project_lead"),
            # Project manager
            func.sum(
                case(
                    (managed_norm.like("project manager%"), 1),
                    else_=0,
                )
            ).label("project_manager"),
            # Team of PM professionals
            func.sum(
                case(
                    (managed_norm.like("team of pm%"), 1),
                    else_=0,
                )
            ).label("team_of_PM_professionals"),
        )
        .where(Project.created_at.isnot(None))
        .group_by(month_expr)
        .order_by(month_expr)
    )

    result = await session.execute(stmt)
    rows = result.all()

    if not rows:
        logger.info("KPI: no data for charters-per-month")
        return []

    data: List[Dict[str, Any]] = []
    for row in rows:
        month_dt: datetime = row.month
        month_name = calendar.month_name[month_dt.month]

        data.append(
            {
                "month": month_name,
                "self_managed": row.self_managed or 0,
                "project_lead": row.project_lead or 0,
                "project_manager": row.project_manager or 0,
                "team_of_PM_professionals": row.team_of_PM_professionals or 0,
            }
        )

    logger.info("KPI: generated charters-per-month summary (%d months)", len(data))
    return data
