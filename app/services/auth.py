from datetime import timedelta
from typing import Any
import logging

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy import select, Row, RowMapping
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.schemas.auth import UserCreate, Token
from app.core import security, config
from app.core.email_service import EmailService
from app.db.database import get_db_session
from app.models.user import User

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")
logger = logging.getLogger(__name__)


class AuthService:
    def __init__(self, db_session: AsyncSession = Depends(get_db_session)):
        self.db_session = db_session
        self.email_service = EmailService()

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

        try:
            hashed_password = security.get_password_hash(user_in.password)

            new_user = User(
                username=user_in.username,
                email=user_in.email,
                hashed_password=hashed_password,
                first_name=user_in.first_name,
                last_name=user_in.last_name,
                role=user_in.role,
                date_of_birth=user_in.date_of_birth,
                gender=user_in.gender,
                height_cm=user_in.height_cm,
                weight_kg=user_in.weight_kg,
                blood_type=user_in.blood_type,
                allergies=user_in.allergies,
                existing_conditions=user_in.existing_conditions,
                specialization=(
                    user_in.specialization if user_in.role == "doctor" else None
                ),
                qualifications=(
                    user_in.qualifications if user_in.role == "doctor" else None
                ),
            )

            db_session.add(new_user)
            await db_session.flush()
            await db_session.refresh(new_user)

            try:
                await self.email_service.send_registration_email(
                    user_email=new_user.email, username=new_user.username
                )
            except Exception as email_exc:

                logger.error(
                    f"Failed to send registration email to {new_user.email}: {email_exc}"
                )

            await db_session.commit()
            await db_session.refresh(new_user)

            access_token_expires = timedelta(
                minutes=config.settings.access_token_expire_minutes
            )
            access_token = security.create_access_token(
                data={"sub": str(new_user.id)}, expires_delta=access_token_expires
            )

            return Token(
                access_token=access_token, token_type="bearer", user_id=new_user.id
            )

        except HTTPException as http_exc:

            raise http_exc
        except Exception as exc:
            logger.error(
                f"Error during user registration for {user_in.username}: {exc}"
            )
            await db_session.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="An unexpected error occurred during registration.",
            )

    async def login_user(
        self, form_data: OAuth2PasswordRequestForm, db_session: AsyncSession
    ) -> Token:
        """Logs in an existing user."""

        try:
            query = select(User).where(User.username == form_data.username)
            result = await db_session.execute(query)
            user = result.scalars().first()

            if not user or not security.verify_password(
                form_data.password, user.hashed_password
            ):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Incorrect username or password",
                    headers={"WWW-Authenticate": "Bearer"},
                )

            access_token_expires = timedelta(
                minutes=config.settings.access_token_expire_minutes
            )
            access_token = security.create_access_token(
                data={"sub": str(user.id)}, expires_delta=access_token_expires
            )

            return Token(
                access_token=access_token, token_type="bearer", user_id=user.id
            )
        except HTTPException as http_exc:
            raise http_exc
        except Exception as exc:
            logger.error(
                f"Error during login attempt for user {form_data.username}: {exc}"
            )

            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="An unexpected error occurred during login.",
            )

    async def get_current_user(
        self, token: str = Depends(oauth2_scheme)
    ) -> Row[Any] | RowMapping:
        """Retrieves the current user from the JWT token."""

        credentials_exception = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
        try:
            payload = security.decode_access_token(token)
            if payload is None:
                logger.warning("Invalid or expired token received.")
                raise credentials_exception

            user_id_str = payload.get("sub")
            if user_id_str is None:
                logger.warning("Token payload missing 'sub' (user ID).")
                raise credentials_exception

            try:
                user_id = int(user_id_str)
            except ValueError:
                logger.warning(f"Invalid user ID format in token: {user_id_str}")
                raise credentials_exception

            query = select(User).where(User.id == user_id)
            result = await self.db_session.execute(query)
            user = result.scalars().first()

            if not user:
                logger.warning(f"User not found for ID extracted from token: {user_id}")
                raise credentials_exception

            return user
        except HTTPException as http_exc:

            raise http_exc
        except Exception as exc:
            logger.error(f"Unexpected error retrieving current user from token: {exc}")

            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Could not retrieve user information.",
            )
