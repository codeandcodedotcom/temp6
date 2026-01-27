import pytest
from unittest.mock import AsyncMock, MagicMock
from datetime import datetime

from app.services import user_service
from app.schemas import User
from app.models.pydantic_models import UserCreate


# ------------------------------------------------------------------
# get_user_by_email
# ------------------------------------------------------------------

@pytest.mark.asyncio
async def test_get_user_by_email_found():
    session = AsyncMock()

    dummy_user = User(
        user_id="550e8400-e29b-41d4-a716-446655440000",
        user_name="Test User",
        email="test@example.com",
        department="IT",
        role="admin",
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )

    # result.scalars().first() chain
    scalars = MagicMock()
    scalars.first.return_value = dummy_user

    result = MagicMock()
    result.scalars.return_value = scalars

    session.execute.return_value = result

    user = await user_service.get_user_by_email(session, "test@example.com")

    assert user == dummy_user
    session.execute.assert_called_once()


@pytest.mark.asyncio
async def test_get_user_by_email_not_found():
    session = AsyncMock()

    scalars = MagicMock()
    scalars.first.return_value = None

    result = MagicMock()
    result.scalars.return_value = scalars

    session.execute.return_value = result

    user = await user_service.get_user_by_email(session, "missing@example.com")

    assert user is None
    session.execute.assert_called_once()


# ------------------------------------------------------------------
# create_or_update_user
# ------------------------------------------------------------------

@pytest.mark.asyncio
async def test_create_or_update_user_updates_existing(monkeypatch):
    session = AsyncMock()

    existing_user = User(
        user_id="550e8400-e29b-41d4-a716-446655440000",
        user_name="Old Name",
        email="test@example.com",
        department="Old Dept",
        role="user",
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )

    payload = UserCreate(
        user_id="550e8400-e29b-41d4-a716-446655440000",
        user_name="New Name",
        email="test@example.com",
        department="IT",
        role="admin",
    )

    async def mock_get_user_by_email(*args, **kwargs):
        return existing_user

    monkeypatch.setattr(
        user_service,
        "get_user_by_email",
        mock_get_user_by_email
    )

    result = await user_service.create_or_update_user(session, payload)

    assert result is existing_user
    assert result.user_name == "New Name"
    assert result.department == "IT"
    assert result.role == "admin"

    session.flush.assert_awaited_once()
    session.add.assert_not_called()


@pytest.mark.asyncio
async def test_create_or_update_user_creates_new(monkeypatch):
    session = AsyncMock()

    payload = UserCreate(
        user_id="550e8400-e29b-41d4-a716-446655440111",
        user_name="New User",
        email="new@example.com",
        department="IT",
        role="user",
    )

    async def mock_get_user_by_email(*args, **kwargs):
        return None

    monkeypatch.setattr(
        user_service,
        "get_user_by_email",
        mock_get_user_by_email
    )

    result = await user_service.create_or_update_user(session, payload)

    assert result.email == "new@example.com"
    assert result.user_name == "New User"
    assert result.department == "IT"
    assert result.role == "user"

    session.add.assert_called_once()
    session.flush.assert_awaited_once()
