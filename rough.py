month_expr = func.date_trunc("month", Project.created_at).label("month")

stmt = (
    select(
        month_expr,

        func.sum(
            case(
                (func.lower(func.trim(Project.managed_by)) == "self managed", 1),
                else_=0,
            )
        ).label("self_managed"),

        func.sum(
            case(
                (func.lower(func.trim(Project.managed_by)).in_(["project lead", "it project lead"]), 1),
                else_=0,
            )
        ).label("team_lead"),

        func.sum(
            case(
                (func.lower(func.trim(Project.managed_by)) == "project manager", 1),
                else_=0,
            )
        ).label("project_manager"),

        func.sum(
            case(
                (func.lower(func.trim(Project.managed_by)) == "team of pm professionals", 1),
                else_=0,
            )
        ).label("team_of_PM_professionals"),
    )
    .group_by(month_expr)
    .order_by(month_expr)
)
