from pydantic import BaseModel, EmailStr


class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str
    first_name: str = None
    last_name: str = None


class Token(BaseModel):
    access_token: str
    token_type: str
