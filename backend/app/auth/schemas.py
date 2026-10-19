from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

Instrument = Literal["piano", "guitar", "drums"]


class RegisterIn(BaseModel):
    email: str = Field(max_length=320)
    password: str = Field(max_length=200)
    display_name: str = Field(min_length=1, max_length=160)


class LoginIn(BaseModel):
    email: str = Field(max_length=320)
    password: str = Field(max_length=200)


class UserOut(BaseModel):
    id: str
    email: str | None
    display_name: str
    role: Literal["learner", "admin"]
    preferred_instrument: Instrument | None
    goal_text: str | None


class AuthOut(BaseModel):
    access_token: str
    token_type: Literal["bearer"] = "bearer"
    expires_in: int
    user: UserOut


class ProfilePatchIn(BaseModel):
    display_name: str | None = Field(default=None, min_length=1, max_length=160)
    preferred_instrument: Instrument | None = None
