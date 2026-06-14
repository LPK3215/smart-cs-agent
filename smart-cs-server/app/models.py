"""Pydantic request/response models."""

from pydantic import BaseModel, Field
from typing import Optional


class ChatRequest(BaseModel):
    sessionId: str
    message: str = Field(..., min_length=1, max_length=1000)


class SessionCreate(BaseModel):
    userId: str | None = None


class SessionUpdate(BaseModel):
    title: Optional[str] = None
    status: Optional[str] = None
    summary: Optional[str] = None


class RatingCreate(BaseModel):
    sessionId: str
    msgId: str
    score: int = Field(..., ge=1, le=5)


class SessionClose(BaseModel):
    sessionId: str
