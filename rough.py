@router.get("/kpi/debug/charters-structure-detailed")
async def get_charters_structure_detailed(session: AsyncSession = Depends(get_db_session)):
    result = await session.execute(text("""
        SELECT 
            column_name, 
            data_type, 
            is_nullable,
            column_default
        FROM information_schema.columns
        WHERE table_name = 'charters'
    """))

    return [dict(row._mapping) for row in result]
