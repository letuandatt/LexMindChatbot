from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List


class SessionCreate(BaseModel):
    """Schema for creating a new chat session"""
    title: Optional[str] = Field(None, max_length=200)


class SessionUpdate(BaseModel):
    """Schema for updating session (e.g., rename)"""
    title: Optional[str] = Field(None, max_length=200)


class MessageResponse(BaseModel):
    """Schema for a single message in history"""
    question: str
    answer: str
    image_gridfs_id: Optional[str] = None
    timestamp: datetime


class SessionResponse(BaseModel):
    """Schema for session list response"""
    session_id: str
    title: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    num_messages: int = 0


class SessionDetailResponse(BaseModel):
    """Schema for session detail with messages"""
    session_id: str
    title: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    messages: List[MessageResponse] = []
