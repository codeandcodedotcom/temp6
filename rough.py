norm = func.lower(func.trim(Project.managed_by))

func.sum(case(norm == "self managed", 1, else_=0)).label("self_managed"),

func.sum(case(norm.in_(["project lead","it project lead"]), 1, else_=0)).label("team_lead"),

func.sum(case(norm == "project manager", 1, else_=0)).label("project_manager"),

func.sum(case(norm == "team of pm professionals", 1, else_=0)).label("team_of_PM_professionals"),
