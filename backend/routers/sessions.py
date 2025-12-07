"""
Sessions Router
Handles chat session management
"""
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status

from backend.models.session import (
    SessionCreate, SessionUpdate, SessionResponse, SessionDetailResponse
)
from backend.dependencies import get_current_user
from backend.services.session_service import (
    get_user_sessions, get_session_detail, create_session,
    update_session_title, delete_session, delete_all_user_sessions
)


router = APIRouter(prefix="/sessions", tags=["Sessions"])


@router.get(
    "/",
    response_model=List[SessionResponse],
    summary="List all chat sessions",
    description="Get all chat sessions for the current user"
)
async def list_sessions(
    limit: int = 50,
    skip: int = 0,
    current_user: dict = Depends(get_current_user)
):
    """
    Get all chat sessions for the current user.
    
    - **limit**: Maximum number of sessions to return (default: 50)
    - **skip**: Number of sessions to skip for pagination (default: 0)
    
    Sessions are ordered by most recent activity first.
    """
    user_id = str(current_user["_id"])
    sessions = get_user_sessions(user_id, limit=limit, skip=skip)
    
    return [SessionResponse(**s) for s in sessions]


@router.post(
    "/",
    response_model=SessionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new chat session",
    description="Create a new chat session for the current user"
)
async def create_new_session(
    session_data: SessionCreate,
    current_user: dict = Depends(get_current_user)
):
    """
    Create a new chat session.
    
    - **title**: Optional title for the session (auto-generated if not provided)
    """
    import uuid
    
    user_id = str(current_user["_id"])
    session_id = str(uuid.uuid4())
    
    session = create_session(
        session_id=session_id,
        user_id=user_id,
        title=session_data.title
    )
    
    return SessionResponse(
        session_id=session["session_id"],
        title=session.get("title"),
        created_at=session.get("created_at"),
        updated_at=session.get("updated_at"),
        num_messages=0
    )


@router.get(
    "/{session_id}",
    response_model=SessionDetailResponse,
    summary="Get session details",
    description="Get a specific session with all messages"
)
async def get_session(
    session_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Get details of a specific chat session including all messages.
    """
    user_id = str(current_user["_id"])
    session = get_session_detail(session_id, user_id)
    
    if session is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )
    
    return SessionDetailResponse(**session)


@router.put(
    "/{session_id}",
    response_model=dict,
    summary="Update session",
    description="Update session title"
)
async def update_session(
    session_id: str,
    update_data: SessionUpdate,
    current_user: dict = Depends(get_current_user)
):
    """
    Update a chat session (e.g., rename it).
    """
    user_id = str(current_user["_id"])
    
    if update_data.title:
        success = update_session_title(session_id, user_id, update_data.title)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Session not found"
            )
    
    return {"message": "Session updated successfully"}


@router.delete(
    "/{session_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete session",
    description="Delete a specific chat session"
)
async def remove_session(
    session_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Delete a specific chat session and all its messages.
    """
    user_id = str(current_user["_id"])
    success = delete_session(session_id, user_id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )
    
    return None


@router.delete(
    "/",
    status_code=status.HTTP_200_OK,
    summary="Delete all sessions",
    description="Delete all chat sessions for the current user"
)
async def remove_all_sessions(
    current_user: dict = Depends(get_current_user)
):
    """
    Delete all chat sessions for the current user.
    
    **Warning**: This will permanently delete all chat history.
    """
    user_id = str(current_user["_id"])
    deleted_count = delete_all_user_sessions(user_id)
    
    return {"message": f"Deleted {deleted_count} sessions"}
