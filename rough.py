@router.get("/debug/alembic-history")
async def alembic_history(session: AsyncSession = Depends(get_db_session)):
    result = await session.execute(
        text("SELECT * FROM alembic_version")
    )
    rows = result.fetchall()
    return {"versions": [row[0] for row in rows]}
