@router.post("/fix-question-6-options")
async def fix_question_6_options():
    from sqlalchemy import text
    from app.db.session import get_db
    from fastapi import HTTPException

    db = next(get_db())

    try:
        updates = [
            {
                "option_id": "99e420ae-2344-46cc-86b0-e39ebf9027c0",
                "new_text": "No, although my function often relies on military funding",
            },
            {
                "option_id": "23a50d39-9c81-474e-bf6e-0670cef58404",
                "new_text": "Yes, it is fully funded",
            },
            {
                "option_id": "c2c7bb97-712a-4f4a-909d-e6b47a8576bf",
                "new_text": "No, my function is not supported by military funding",
            },
        ]

        total_updated = 0

        for item in updates:
            result = db.execute(
                text("""
                    UPDATE question_options
                    SET option_text = :new_text
                    WHERE option_id = :option_id
                """),
                {
                    "new_text": item["new_text"],
                    "option_id": item["option_id"],
                }
            )
            total_updated += result.rowcount

        db.commit()

        return {
            "message": "Options updated successfully",
            "rows_updated": total_updated
        }

    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Update failed: {str(e)}"
        )



