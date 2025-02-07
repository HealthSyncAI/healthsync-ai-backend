from datetime import datetime, timedelta

import jwt
from jwt import PyJWTError
from passlib.context import CryptContext

from app.core.config import settings

# Initialize the password hashing context with bcrypt
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def get_password_hash(password: str) -> str:
    """
    Hash a plain-text password for secure storage.
    """
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Validate a plain-text password against the stored hash.
    """
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(data: dict, expires_delta: timedelta = None) -> str:
    """
    Create a JWT token with an expiration.
    Expects a dictionary (e.g., with user id under key "sub").
    """
    to_encode = data.copy()
    expire = datetime.utcnow() + (
        expires_delta
        if expires_delta
        else timedelta(minutes=settings.access_token_expire_minutes)
    )
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(
        to_encode, settings.jwt_secret_key, algorithm=settings.jwt_algorithm
    )
    return encoded_jwt


def decode_access_token(token: str) -> dict:
    """
    Decode and verify a JWT token. Returns the payload if valid; otherwise, returns None.
    """
    try:
        payload = jwt.decode(
            token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm]
        )
        return payload
    except PyJWTError:
        # In production, log the exception details securely.
        return None
