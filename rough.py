stmt = (
    select(
        month_expr,

        func.sum(case((Project.managed_by == "Self Managed", 1), else_=0)).label("self_managed"),
        func.sum(case((Project.managed_by.in_(["Project Lead","IT Project Lead"]), 1), else_=0)).label("team_lead"),
        func.sum(case((Project.managed_by == "Project Manager", 1), else_=0)).label("project_manager"),
        func.sum(case((Project.managed_by == "Team of PM professionals", 1), else_=0)).label("team_of_PM_professionals"),
    )
    .group_by(month_expr)
    .order_by(month_expr)
)
