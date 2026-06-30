from pydantic import BaseModel, EmailStr, Field
from pydantic import field_validator
from pydantic.config import ConfigDict
from uuid import UUID

class RegisterRequest(BaseModel):
    email : EmailStr = Field(...)
    password : str = Field(..., min_length=8)

class LoginRequest(BaseModel):
    email : EmailStr = Field(...)
    password : str = Field(..., min_length=8)

class TokenResponse(BaseModel):
    access_token : str
    refresh_token : str 
    token_type : str = "bearer"

class RefreshRequest(BaseModel):
    refresh_token : str

class UserResponse(BaseModel):
    id : UUID
    email : EmailStr
    role : str
    is_active : bool
    model_config = ConfigDict(from_attributes=True)
