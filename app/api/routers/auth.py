from fastapi import APIRouter, Depends, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.schemas.auth import UserCreate, Token
from app.db.database import get_db_session
from app.services.auth import AuthService

router = APIRouter()


@router.post("/register", response_model=Token, status_code=status.HTTP_201_CREATED)
async def register(
    user_in: UserCreate,
    db_session: AsyncSession = Depends(get_db_session),
    auth_service: AuthService = Depends(AuthService),
):
    """
    Registration endpoint for new users.
    """
    return await auth_service.register_user(user_in, db_session)


@router.post("/login", response_model=Token)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db_session: AsyncSession = Depends(get_db_session),
    auth_service: AuthService = Depends(AuthService),
):
    """
    Login endpoint for user authentication.
    """
    return await auth_service.login_user(form_data, db_session)
