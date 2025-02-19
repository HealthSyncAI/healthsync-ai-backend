from datetime import timedelta

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.schemas.auth import UserCreate, Token
from app.core import security, config
from app.db.database import get_db_session
from app.models.user import User, UserRole

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


class AuthService:
    def __init__(self, db_session: AsyncSession = Depends(get_db_session)):
        self.db_session = db_session

    async def register_user(
        self, user_in: UserCreate, db_session: AsyncSession
    ) -> Token:
        """Registers a new user, handling additional health information."""

        query = select(User).where(
            (User.email == user_in.email) | (User.username == user_in.username)
        )
        result = await db_session.execute(query)
        existing_user = result.scalars().first()

        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="A user with this email or username already exists",
            )

        hashed_password = security.get_password_hash(user_in.password)

        new_user = User(
            username=user_in.username,
            email=user_in.email,
            hashed_password=hashed_password,
            first_name=user_in.first_name,
            last_name=user_in.last_name,
            role=UserRole.patient,  # Default to patient, as before
            date_of_birth=user_in.date_of_birth,
            gender=user_in.gender,
            height_cm=user_in.height_cm,
            weight_kg=user_in.weight_kg,
            blood_type=user_in.blood_type,
            allergies=user_in.allergies,
            existing_conditions=user_in.existing_conditions,
        )

        db_session.add(new_user)
        await db_session.commit()
        await db_session.refresh(new_user)

        access_token_expires = timedelta(
            minutes=config.settings.access_token_expire_minutes
        )
        access_token = security.create_access_token(
            data={"sub": str(new_user.id)}, expires_delta=access_token_expires
        )

        return Token(access_token=access_token, token_type="bearer")

    async def login_user(
        self, form_data: OAuth2PasswordRequestForm, db_session: AsyncSession
    ) -> Token:
        """Logs in an existing user."""
        query = select(User).where(User.username == form_data.username)
        result = await db_session.execute(query)
        user = result.scalars().first()

        if not user or not security.verify_password(
            form_data.password, user.hashed_password
        ):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Incorrect username or password",
            )

        access_token_expires = timedelta(
            minutes=config.settings.access_token_expire_minutes
        )
        access_token = security.create_access_token(
            data={"sub": str(user.id)}, expires_delta=access_token_expires
        )

        return Token(access_token=access_token, token_type="bearer")

    async def get_current_user(self, token: str = Depends(oauth2_scheme)) -> User:
        """Retrieves the current user from the JWT token."""
        payload = security.decode_access_token(token)
        if payload is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired token",
            )
        user_id = payload.get("sub")
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token payload"
            )

        query = select(User).where(User.id == int(user_id))
        result = await self.db_session.execute(query)  # Use self.db_session
        user = result.scalars().first()

        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found"
            )
        return user
