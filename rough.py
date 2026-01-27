import pytest
from unittest.mock import AsyncMock

from app.services import user_service
from app.models.pydantic_models import UserCreate
from app.schemas import User


@pytest.mark.asyncio
async def test_get_user_by_email_found():
    session = AsyncMock()

    mock_user = User(
        user_id="123e4567e89b12d3a456426614174000",
        user_name="Test User",
        email="test@example.com",
        department="HR",
        role="Admin",
    )

    result = AsyncMock()
    result.scalars.return_value.first.return_value = mock_user
    session.execute.return_value = result

    user = await user_service.get_user_by_email(session, "test@example.com")

    assert user == mock_user
    session.execute.assert_called_once()


@pytest.mark.asyncio
async def test_get_user_by_email_not_found():
    session = AsyncMock()

    result = AsyncMock()
    result.scalars.return_value.first.return_value = None
    session.execute.return_value = result

    user = await user_service.get_user_by_email(session, "missing@example.com")

    assert user is None


@pytest.mark.asyncio
async def test_create_or_update_user_creates_new(monkeypatch):
    session = AsyncMock()

    monkeypatch.setattr(
        user_service,
        "get_user_by_email",
        AsyncMock(return_value=None),
    )

    payload = UserCreate(
        user_id="123e4567e89b12d3a456426614174000",
        user_name="New User",
        email="new@example.com",
        department="HR",
        role="Admin",
    )

    user = await user_service.create_or_update_user(session, payload)

    session.add.assert_called_once()
    session.flush.assert_called()
    assert user.email == "new@example.com"


@pytest.mark.asyncio
async def test_create_or_update_user_updates_existing(monkeypatch):
    session = AsyncMock()

    existing_user = User(
        user_id="123e4567e89b12d3a456426614174000",
        user_name="Old Name",
        email="existing@example.com",
        department="IT",
        role="User",
    )

    monkeypatch.setattr(
        user_service,
        "get_user_by_email",
        AsyncMock(return_value=existing_user),
    )

    payload = UserCreate(
        user_id="123e4567e89b12d3a456426614174000",
        user_name="Updated Name",
        email="existing@example.com",
        department="HR",
        role="Admin",
    )

    user = await user_service.create_or_update_user(session, payload)

    assert user.user_name == "Updated Name"
    assert user.department == "HR"
    assert user.role == "Admin"
    session.flush.assert_called()
