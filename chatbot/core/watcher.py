import threading
import time
import os
import tempfile
from bson.objectid import ObjectId
from pymongo.errors import OperationFailure
import google.genai as genai

from chatbot.core.db import DB_DOCUMENTS_COLLECTION, FS
from chatbot.core.file_store import process_and_vectorize_pdf
from chatbot.config import config as app_config


class DatabaseWatcher:
    def __init__(self):
        self._stop_event = threading.Event()
        self.thread = None
        try:
            self.genai_client = genai.Client(api_key=app_config.GOOGLE_API_KEY)
        except Exception as e:
            print(f"❌ [Watcher] Lỗi khởi tạo GenAI Client: {e}")
            self.genai_client = None

    def _process_single_file(self, doc):
        """Logic xử lý 1 file: Tải từ GridFS -> Upload Google -> Clean"""
        filename = doc.get("filename", "unknown.pdf")
        gridfs_id = doc.get("file_gridfs_id")
        session_id = doc.get("session_id")

        print(f"🔔 [Watcher] Phát hiện file mới: {filename}")

        if not gridfs_id:
            print(f"⚠️ [Watcher] File {filename} thiếu GridFS ID. Bỏ qua.")
            return

        temp_path = None
        try:
            # 1. Lấy file từ GridFS
            grid_out = FS.get(ObjectId(gridfs_id))

            # 2. Ghi ra file tạm
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
                tmp_file.write(grid_out.read())
                temp_path = tmp_file.name

            # 3. Xử lý
            if self.genai_client:
                process_and_vectorize_pdf(
                    file_path=temp_path,
                    session_id=session_id,
                    doc_id=str(doc["_id"]),
                    genai_client=self.genai_client
                )
                print(f"✅ [Watcher] Xử lý hoàn tất: {filename}")
            else:
                print("❌ [Watcher] GenAI Client chưa sẵn sàng.")

        except Exception as e:
            print(f"❌ [Watcher] Lỗi khi xử lý file {filename}: {e}")
            # Cập nhật trạng thái lỗi để không retry vô tận
            DB_DOCUMENTS_COLLECTION.update_one(
                {"_id": doc["_id"]},
                {"$set": {"status": "error", "error_msg": str(e)}}
            )
        finally:
            # 4. Dọn dẹp
            if temp_path and os.path.exists(temp_path):
                try:
                    os.remove(temp_path)
                except Exception:
                    pass

    def _poll_documents(self):
        """Chế độ Fallback: Quét DB mỗi 5 giây (Dùng cho Standalone Mongo)"""
        print("⚠️ [Watcher] Chuyển sang chế độ POLLING (Quét định kỳ 5s)...")
        while not self._stop_event.is_set():
            try:
                # Tìm các file có status = 'uploaded'
                cursor = DB_DOCUMENTS_COLLECTION.find({"status": "uploaded"})
                for doc in cursor:
                    if self._stop_event.is_set(): break
                    self._process_single_file(doc)

                # Ngủ 5 giây rồi quét tiếp
                time.sleep(5)
            except Exception as e:
                print(f"❌ [Watcher] Polling Error: {e}")
                time.sleep(5)

    def _watch_documents(self):
        """Chế độ Chính: Lắng nghe sự kiện Realtime (Cần Replica Set)"""
        print("👀 [Watcher] Đang thử kích hoạt chế độ Realtime Stream...")

        if DB_DOCUMENTS_COLLECTION is None or FS is None:
            print("❌ [Watcher] Lỗi: Không kết nối được DB/GridFS.")
            return

        pipeline = [{"$match": {"operationType": {"$in": ["insert", "update"]}}}]

        try:
            with DB_DOCUMENTS_COLLECTION.watch(pipeline) as stream:
                print("✅ [Watcher] Đã kết nối Realtime Stream thành công.")
                for change in stream:
                    if self._stop_event.is_set(): break

                    doc = change.get("fullDocument")
                    if not doc:
                        try:
                            doc_id = change["documentKey"]["_id"]
                            doc = DB_DOCUMENTS_COLLECTION.find_one({"_id": doc_id})
                        except Exception:
                            continue

                    if doc and doc.get("status") == "uploaded":
                        self._process_single_file(doc)

        except OperationFailure as e:
            # Mã lỗi 40573: The $changeStream stage is only supported on replica sets
            if e.code == 40573:
                print(f"ℹ️ [Watcher] MongoDB đang chạy Standalone (không hỗ trợ Stream).")
                self._poll_documents()  # <-- Fallback sang Polling
            else:
                print(f"❌ [Watcher] Lỗi Stream khác: {e}")
                time.sleep(5)
                self._poll_documents()  # Fallback an toàn

        except Exception as e:
            print(f"❌ [Watcher] Lỗi không xác định: {e}")
            self._poll_documents()

    def start(self):
        if self.thread and self.thread.is_alive(): return
        self._stop_event.clear()
        self.thread = threading.Thread(target=self._watch_documents, daemon=True)
        self.thread.start()

    def stop(self):
        self._stop_event.set()
        print("🛑 [Watcher] Đang dừng dịch vụ...")


# Singleton
app_watcher = DatabaseWatcher()