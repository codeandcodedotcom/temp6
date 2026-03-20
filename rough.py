from sqlalchemy import text

@router.post("/kpi/debug/add-column")
async def add_column(session: AsyncSession = Depends(get_db_session)):
    try:
        await session.execute(text("""
            ALTER TABLE charters 
            ADD COLUMN generation_started_at TIMESTAMP WITH TIME ZONE
        """))
        await session.commit()
        return {"status": "column added successfully"}
    except Exception as e:
        await session.rollback()
        return {"error": str(e)}


await session.execute(text("""
    ALTER TABLE charters 
    ADD COLUMN IF NOT EXISTS generation_started_at TIMESTAMP WITH TIME ZONE
"""))
