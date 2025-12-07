from pymongo import MongoClient, ASCENDING, DESCENDING
import gridfs
from chatbot.config import config as app_config

_mongo_client = None
_mongo_db = None
DB_COLLECTION = None
DB_DOCUMENTS_COLLECTION = None
DB_USERS_COLLECTION = None
FS = None

def init_db():
    global _mongo_client, _mongo_db, DB_COLLECTION, DB_DOCUMENTS_COLLECTION, DB_USERS_COLLECTION, FS
    try:
        _mongo_client = MongoClient(app_config.MONGO_URI, serverSelectionTimeoutMS=5000, connectTimeoutMS=5000)
        _mongo_client.admin.command('ping')
        _mongo_db = _mongo_client[app_config.MONGO_DB_NAME]
        DB_COLLECTION = _mongo_db.get_collection("sessions")
        FS = gridfs.GridFS(_mongo_db)
        # safe index ops
        try:
            DB_COLLECTION.create_index([("session_id", ASCENDING)], unique=True)
        except Exception:
            pass
        try:
            DB_COLLECTION.create_index([("updated_at", DESCENDING)])
        except Exception:
            pass
        # documents collection
        DB_DOCUMENTS_COLLECTION = _mongo_db.get_collection("documents")
        try:
            existing_indexes = DB_DOCUMENTS_COLLECTION.index_information()
            for idx_name, idx_info in existing_indexes.items():
                # remove legacy unique file_hash if exists
                if idx_name.startswith("file_hash_") and idx_info.get("unique", False):
                    try:
                        DB_DOCUMENTS_COLLECTION.drop_index(idx_name)
                    except Exception:
                        pass
            # create non-unique file_hash index
            try:
                DB_DOCUMENTS_COLLECTION.create_index([("file_hash", 1)], name="file_hash_idx", background=True)
            except Exception:
                pass
        except Exception:
            # if documents collection not ready, ignore
            pass
        
        # users collection
        DB_USERS_COLLECTION = _mongo_db.get_collection("users")
        try:
            DB_USERS_COLLECTION.create_index([("email", ASCENDING)], unique=True)
        except Exception:
            pass
        
        print("[core.db] MongoDB initialized.")
    except Exception as e:
        print(f"[core.db] Failed to initialize MongoDB: {e}")
        _mongo_client = _mongo_db = DB_COLLECTION = DB_DOCUMENTS_COLLECTION = FS = None


# initialize on import
init_db()

def get_mongo_collection(collection_name="sessions"):
    """
    Return collection object or None.
    """
    global _mongo_db
    if _mongo_db is None:
        return None
    return _mongo_db.get_collection(collection_name)
