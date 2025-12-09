"""
Session Service
Handles chat session CRUD operations
"""
from datetime import datetime
from typing import Optional, List
from bson import ObjectId

from chatbot.core.db import get_mongo_collection
from pymongo import DESCENDING
from datetime import timezone, timedelta

# Vietnam timezone (UTC+7)
VN_TIMEZONE = timezone(timedelta(hours=7))

def get_vn_now():
    """Get current time in Vietnam timezone"""
    return datetime.now(VN_TIMEZONE)


def get_user_sessions(user_id: str, limit: int = 50, skip: int = 0) -> List[dict]:
    """
    Get all sessions for a user, ordered by most recent first
    """
    coll = get_mongo_collection("sessions")
    if coll is None:
        return []
    
    sessions = coll.find(
        {"user_id": user_id},
        projection={
            "session_id": 1,
            "title": 1,
            "created_at": 1,
            "updated_at": 1,
            "messages": 1
        }
    ).sort("updated_at", DESCENDING).skip(skip).limit(limit)
    
    return [{
        "session_id": s["session_id"],
        "title": s.get("title"),
        "created_at": s.get("created_at"),
        "updated_at": s.get("updated_at"),
        "num_messages": len(s.get("messages", []))
    } for s in sessions]


def get_session_detail(session_id: str, user_id: str) -> Optional[dict]:
    """
    Get a single session with all messages
    """
    coll = get_mongo_collection("sessions")
    if coll is None:
        return None
    
    session = coll.find_one({"session_id": session_id, "user_id": user_id})
    if not session:
        return None
    
    return {
        "session_id": session["session_id"],
        "title": session.get("title"),
        "created_at": session.get("created_at"),
        "updated_at": session.get("updated_at"),
        "messages": session.get("messages", [])
    }


def create_session(session_id: str, user_id: str, title: Optional[str] = None) -> dict:
    """
    Create a new chat session
    """
    coll = get_mongo_collection("sessions")
    now = get_vn_now()
    
    session_doc = {
        "session_id": session_id,
        "user_id": user_id,
        "title": title or f"Chat {now.strftime('%Y-%m-%d %H:%M')}",
        "created_at": now,
        "updated_at": now,
        "messages": []
    }
    
    if coll is not None:
        try:
            coll.insert_one(session_doc)
        except Exception as e:
            print(f"[session_service] Error creating session: {e}")
    
    return session_doc


def update_session_title(session_id: str, user_id: str, title: str) -> bool:
    """
    Update session title
    """
    coll = get_mongo_collection("sessions")
    if coll is None:
        return False
    
    try:
        result = coll.update_one(
            {"session_id": session_id, "user_id": user_id},
            {"$set": {"title": title, "updated_at": get_vn_now()}}
        )
        return result.modified_count > 0
    except Exception as e:
        print(f"[session_service] Error updating session: {e}")
        return False


def delete_session(session_id: str, user_id: str) -> bool:
    """
    Delete a chat session
    """
    coll = get_mongo_collection("sessions")
    if coll is None:
        return False
    
    try:
        result = coll.delete_one({"session_id": session_id, "user_id": user_id})
        return result.deleted_count > 0
    except Exception as e:
        print(f"[session_service] Error deleting session: {e}")
        return False


def delete_all_user_sessions(user_id: str) -> int:
    """
    Delete all sessions for a user
    Returns number of deleted sessions
    """
    coll = get_mongo_collection("sessions")
    if coll is None:
        return 0
    
    try:
        result = coll.delete_many({"user_id": user_id})
        return result.deleted_count
    except Exception as e:
        print(f"[session_service] Error deleting sessions: {e}")
        return 0
