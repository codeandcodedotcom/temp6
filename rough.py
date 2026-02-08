def test_backend_ignored_scores_fallbacks_to_frontend():
    questions = [
        {"score": 10},
        {"score": 5},
    ]

    total, budget, project_type, product_type = _compute_total_score(
        questions,
        frontend_total_score=99,
    )

    # Backend ignores these scores → fallback must happen
    assert total == 99
    assert budget is None
    assert project_type is None
    assert product_type is None
