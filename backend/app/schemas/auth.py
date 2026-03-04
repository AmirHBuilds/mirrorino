from pydantic import BaseModel, EmailStr, field_validator
import re

class CaptchaResponse(BaseModel):
    captcha_id: str
    image_base64: str

class RegisterRequest(BaseModel):
    username: str
    email: EmailStr
    password: str
    captcha_id: str
    captcha_answer: str

    @field_validator("username")
    @classmethod
    def username_valid(cls, v):
        if not re.match(r"^[a-zA-Z0-9_]{3,50}$", v):
            raise ValueError("Username must be 3-50 chars, letters/numbers/underscore only")
        return v.lower()

    @field_validator("password")
    @classmethod
    def password_strong(cls, v):
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters")
        return v

class LoginRequest(BaseModel):
    username: str
    password: str
    captcha_id: str
    captcha_answer: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int

class TokenData(BaseModel):
    user_id: int | None = None
    username: str | None = None
    role: str | None = None
