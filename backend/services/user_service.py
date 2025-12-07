"""
User Service
Handles user CRUD operations
"""
from datetime import datetime
from typing import Optional
from bson import ObjectId

from chatbot.core.db import DB_USERS_COLLECTION, get_mongo_collection
from backend.services.auth_service import hash_password, verify_password


def create_user(email: str, password: str, full_name: Optional[str] = None) -> Optional[dict]:
    """
    Create a new user in the database
    Returns the created user document or None if email already exists
    """
    if DB_USERS_COLLECTION is None:
        print("[user_service] Users collection not initialized")
        return None
    
    # Check if email already exists
    existing = DB_USERS_COLLECTION.find_one({"email": email.lower()})
    if existing:
        return None  # Email already registered
    
    user_doc = {
        "email": email.lower(),
        "hashed_password": hash_password(password),
        "full_name": full_name,
        "avatar_url": None,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
        "is_active": True,
        "is_verified": False,  # For future email verification
        "preferences": {}  # User preferences/settings
    }
    
    try:
        result = DB_USERS_COLLECTION.insert_one(user_doc)
        user_doc["_id"] = result.inserted_id
        return user_doc
    except Exception as e:
        print(f"[user_service] Error creating user: {e}")
        return None


def authenticate_user(email: str, password: str) -> Optional[dict]:
    """
    Authenticate a user by email and password
    Returns user document if valid, None otherwise
    """
    if DB_USERS_COLLECTION is None:
        return None
    
    user = DB_USERS_COLLECTION.find_one({"email": email.lower()})
    if not user:
        return None
    
    if not user.get("is_active", True):
        return None  # Account is deactivated
    
    if not verify_password(password, user["hashed_password"]):
        return None
    
    return user


def get_user_by_id(user_id: str) -> Optional[dict]:
    """Get a user by their ObjectId string"""
    if DB_USERS_COLLECTION is None:
        return None
    
    try:
        return DB_USERS_COLLECTION.find_one({"_id": ObjectId(user_id)})
    except Exception:
        return None


def get_user_by_email(email: str) -> Optional[dict]:
    """Get a user by their email address"""
    if DB_USERS_COLLECTION is None:
        return None
    
    return DB_USERS_COLLECTION.find_one({"email": email.lower()})


def update_user(user_id: str, update_data: dict) -> Optional[dict]:
    """
    Update user profile
    Returns updated user document or None
    """
    if DB_USERS_COLLECTION is None:
        return None
    
    # Filter out None values and add updated_at
    update_fields = {k: v for k, v in update_data.items() if v is not None}
    update_fields["updated_at"] = datetime.utcnow()
    
    try:
        result = DB_USERS_COLLECTION.find_one_and_update(
            {"_id": ObjectId(user_id)},
            {"$set": update_fields},
            return_document=True
        )
        return result
    except Exception as e:
        print(f"[user_service] Error updating user: {e}")
        return None


def change_password(user_id: str, current_password: str, new_password: str) -> bool:
    """
    Change user password
    Returns True if successful, False otherwise
    """
    if DB_USERS_COLLECTION is None:
        return False
    
    user = get_user_by_id(user_id)
    if not user:
        return False
    
    # Verify current password
    if not verify_password(current_password, user["hashed_password"]):
        return False
    
    # Update to new password
    try:
        DB_USERS_COLLECTION.update_one(
            {"_id": ObjectId(user_id)},
            {
                "$set": {
                    "hashed_password": hash_password(new_password),
                    "updated_at": datetime.utcnow()
                }
            }
        )
        return True
    except Exception as e:
        print(f"[user_service] Error changing password: {e}")
        return False


def delete_user(user_id: str) -> bool:
    """
    Delete a user account (hard delete)
    Returns True if successful
    """
    if DB_USERS_COLLECTION is None:
        return False
    
    try:
        result = DB_USERS_COLLECTION.delete_one({"_id": ObjectId(user_id)})
        
        # Also delete user's sessions
        sessions_coll = get_mongo_collection("sessions")
        if sessions_coll:
            sessions_coll.delete_many({"user_id": user_id})
        
        return result.deleted_count > 0
    except Exception as e:
        print(f"[user_service] Error deleting user: {e}")
        return False


def deactivate_user(user_id: str) -> bool:
    """
    Soft delete - deactivate a user account
    Returns True if successful
    """
    if DB_USERS_COLLECTION is None:
        return False
    
    try:
        result = DB_USERS_COLLECTION.update_one(
            {"_id": ObjectId(user_id)},
            {"$set": {"is_active": False, "updated_at": datetime.utcnow()}}
        )
        return result.modified_count > 0
    except Exception as e:
        print(f"[user_service] Error deactivating user: {e}")
        return False


def verify_user(user_id: str) -> bool:
    """
    Verify a user's email address.
    Sets is_verified = True.
    Returns True if successful.
    """
    if DB_USERS_COLLECTION is None:
        return False
    
    try:
        result = DB_USERS_COLLECTION.update_one(
            {"_id": ObjectId(user_id)},
            {"$set": {"is_verified": True, "updated_at": datetime.utcnow()}}
        )
        return result.modified_count > 0
    except Exception as e:
        print(f"[user_service] Error verifying user: {e}")
        return False


def is_user_verified(user_id: str) -> bool:
    """
    Check if a user's email is verified.
    """
    user = get_user_by_id(user_id)
    if not user:
        return False
    return user.get("is_verified", False)
