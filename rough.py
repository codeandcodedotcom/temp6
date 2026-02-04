from uuid import uuid4
from datetime import datetime

def mock_llm_answer(**_):
    return {
        "project_id": uuid4(),
        "charter_id": uuid4(),
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

        "project_scope": {},
        "budget_breakdown": {"allocation": {}},
        "timeline": {},
        "risks_and_mitigation": [],
        "pm_resource_recommendation": []
    }

monkeypatch.setattr(
    "app.api.generation.get_llm_answer",
    mock_llm_answer
)
