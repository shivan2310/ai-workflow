import uuid
from typing import Optional
from pydantic import BaseModel, Field


class AuthenticatedUser(BaseModel):
    id: uuid.UUID = Field(description="Supabase user UUID extracted from verified JWT")
    email: Optional[str] = Field(default=None, description="User email address if present in token")
    role: Optional[str] = Field(default=None, description="User role if present in token")
    aud: Optional[str] = Field(default=None, description="Audience claim")
