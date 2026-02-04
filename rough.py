def mock_llm_answer(**_):
    return {
        "project_id": uuid.uuid4(),
        "charter_id": uuid.uuid4(),
        "created_at": datetime.utcnow(),

        "project_title": "Test Project",
        "description": "Test description",
        "industry": "IT",
        "duration": "6 months",
        "budget": "100k",
        "complexity_score": 10,
        "project_sponsor": "Sponsor",

        "managed_by": "LLM",
        "charter_pdf_url": "http://example.com/file.pdf",
        "context_used": "unit-test",

        "current_state": [],
        "objectives": [],
        "future_state": [],
        "high_level_requirement": [],
        "business_benefit": [],
        "dependencies": [],
        "lesson_learnt": [],
        "success_criteria": [],
        "assumptions": [],

        "project_scope": {
            "scope": None,
            "in_scope": [],
            "out_scope": [],
        },

        "budget_breakdown": {
            "total_cost": None,
            "allocation": {},
        },

        "timeline": {
            "project_initiation_and_planning": {
                "duration": None,
                "context": None,
                "prerequisites": [],
                "tasks": [],
            },
            "design_and_architecture": None,
            "development_and_implementation": None,
            "testing_and_quality_assurance": None,
            "deployment_and_uat": None,
            "production_deployment": None,
            "project_closure": None,
        },

        "risks_and_mitigation": [],

        "pm_resource_recommendation": [],
    }
