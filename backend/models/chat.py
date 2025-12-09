from pydantic import BaseModel, Field
from typing import Optional, List


class ChatRequest(BaseModel):
    """Schema for chat request (unified - deprecated)"""
    message: str = Field(..., min_length=1, max_length=10000)
    session_id: Optional[str] = None  # If None, create new session
    image_base64: Optional[str] = None  # Optional base64 encoded image


class TextChatRequest(BaseModel):
    """Schema for text-only chat request"""
    message: str = Field(..., min_length=1, max_length=10000)
    session_id: Optional[str] = None


class PdfChatRequest(BaseModel):
    """Schema for PDF-based chat request"""
    message: str = Field(..., min_length=1, max_length=10000)
    session_id: Optional[str] = None
    file_id: Optional[str] = None  # GridFS file ID of uploaded PDF


class ImageChatRequest(BaseModel):
    """Schema for image-based chat request"""
    message: str = Field(..., min_length=1, max_length=10000)
    session_id: Optional[str] = None
    image_base64: str = Field(..., min_length=1)  # Required base64 encoded image


class ThinkingStep(BaseModel):
    """Schema for a single thinking/reasoning step"""
    agent: str  # Agent name (Supervisor, LawResearcher, etc.)
    action: str  # What the agent is doing
    detail: Optional[str] = None  # Additional details


class ChatResponse(BaseModel):
    """Schema for chat response"""
    session_id: str
    response: str
    agent_name: Optional[str] = None
    sources: Optional[List[str]] = None  # References/sources used
    thinking_steps: Optional[List[ThinkingStep]] = None  # Reasoning steps


class StreamChatResponse(BaseModel):
    """Schema for streaming chat response chunk"""
    session_id: str
    chunk: str
    is_final: bool = False
    agent_name: Optional[str] = None


class FileUploadResponse(BaseModel):
    """Schema for file upload response"""
    file_id: str
    filename: str
    status: str
    message: str
