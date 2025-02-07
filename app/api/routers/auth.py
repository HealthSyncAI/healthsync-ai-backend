from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel, EmailStr
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core import security, config
from app.db.database import get_db_session
from app.models.user import User, UserRole

router = APIRouter()


# Pydantic model for user registration input.
class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str
    first_name: str = None
    last_name: str = None


# Pydantic model for the token response.
class Token(BaseModel):
    access_token: str
    token_type: str


# OAuth2 scheme: tokenUrl points to our login endpoint.
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


@router.post("/register", response_model=Token, status_code=status.HTTP_201_CREATED)
async def register(
    user_in: UserCreate, db_session: AsyncSession = Depends(get_db_session)
):
    """
    Registration endpoint for new users.
    - Checks that the username/email is unique.
    - Hashes the user password.
    - Saves the new user record to the DB.
    - Returns an access token upon successful registration.
    """
    # Check if a user with the provided email or username already exists.
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

    # Hash the provided password.
    hashed_password = security.get_password_hash(user_in.password)

    # Create a new user instance (default role is 'patient').
    new_user = User(
        username=user_in.username,
        email=user_in.email,
        hashed_password=hashed_password,
        first_name=user_in.first_name,
        last_name=user_in.last_name,
        role=UserRole.patient,
    )

    db_session.add(new_user)
    await db_session.commit()
    await db_session.refresh(new_user)

    # Create a JWT access token for the new user.
    access_token_expires = timedelta(
        minutes=config.settings.access_token_expire_minutes
    )
    access_token = security.create_access_token(
        data={"sub": str(new_user.id)}, expires_delta=access_token_expires
    )

    return {"access_token": access_token, "token_type": "bearer"}


@router.post("/login", response_model=Token)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db_session: AsyncSession = Depends(get_db_session),
):
    """
    Login endpoint for user authentication.
    - Validates the provided credentials.
    - Returns a JWT access token if authentication is successful.
    """
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

    # Generate JWT token for the authenticated user.
    access_token_expires = timedelta(
        minutes=config.settings.access_token_expire_minutes
    )
    access_token = security.create_access_token(
        data={"sub": str(user.id)}, expires_delta=access_token_expires
    )

    return {"access_token": access_token, "token_type": "bearer"}


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db_session: AsyncSession = Depends(get_db_session),
):
    """
    Dependency to retrieve the current user from the JWT token.
    - Decodes the token.
    - Validates the payload.
    - Returns the associated user.
    """
    payload = security.decode_access_token(token)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token"
        )
    user_id = payload.get("sub")
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token payload"
        )

    query = select(User).where(User.id == int(user_id))
    result = await db_session.execute(query)
    user = result.scalars().first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found"
        )
    return user
