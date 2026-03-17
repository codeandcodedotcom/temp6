from collections import defaultdict
from typing import List, Dict, Any
from sqlalchemy import select
from app.schemas.charter import Charter as DBCharter


async def get_roi_time_monthly(session: AsyncSession) -> List[Dict[str, Any]]:
    stmt = select(
        DBCharter.created_at,
        DBCharter.generation_started_at
    ).where(DBCharter.generation_started_at.isnot(None))

    res = await session.execute(stmt)
    rows = res.all()

    monthly_data = defaultdict(lambda: {"total_sec": 0, "count": 0})

    for created_at, started_at in rows:
        if created_at and started_at:
            duration = (created_at - started_at).total_seconds()
            if duration >= 0:
                # key = year-month (to avoid mixing Jan 2024 & Jan 2025)
                key = created_at.strftime("%Y-%m")
                monthly_data[key]["total_sec"] += duration
                monthly_data[key]["count"] += 1

    result = []

    for key in sorted(monthly_data.keys()):
        total_sec = monthly_data[key]["total_sec"]
        count = monthly_data[key]["count"]

        actual_hours = total_sec / 3600
        estimated_hours = count * 50

        # Convert to readable month
        month_label = key  # default fallback
        try:
            from datetime import datetime
            month_label = datetime.strptime(key, "%Y-%m").strftime("%b %Y")  # Jan 2025
        except Exception:
            pass

        result.append({
            "month": month_label,
            "total_actual_time_hours": round(actual_hours, 2),
            "total_estimated_time_hours": estimated_hours,
            "total_charters": count
        })

    return result




from app.services.kpi_service import get_roi_time_monthly


@router.get("/kpi/roi-time")
async def roi_time(session: AsyncSession = Depends(get_session)):
    try:
        data = await get_roi_time_monthly(session)
        return data
    except Exception:
        logger.exception("Failed to fetch ROI KPI")
        raise HTTPException(
            status_code=500,
            detail="Failed to fetch ROI KPI"
        )
