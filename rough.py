from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Depends
from app.db.session_new import get_db_session
from app.services.project_service import create_project
from app.models.pydantic_models import ProjectCharter  # already imported, keep it




&&---&

@router.post("/generation/ask", response_model=ProjectCharter)
async def ask(
    payload: AskRequest,
    request: Request,
    session: AsyncSession = Depends(get_db_session),
) -> ProjectCharter:

    ---------


# Persist project row using the generated charter JSON
    try:
        charter = ProjectCharter(**response)

        async with session.begin():
            await create_project(
                session=session,
                charter=charter,
                user_id=payload.user_id,
            )
    except Exception:
        # We log but do NOT break the charter generation for the user
        logger.exception(
            "Failed to create project record for project_id=%s", response.get("project_id")
)
