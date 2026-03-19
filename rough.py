@router.get("/debug/db-check")
async def check_column(session: AsyncSession = Depends(get_db_session)):
    result = await session.execute(
        text("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'charter'
            AND column_name = 'generation_started_at'
        """)
    )
    return {"exists": bool(result.scalar())}
