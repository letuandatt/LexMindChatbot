import os
import uuid
import time
import google.genai as genai
from langchain_core.messages import HumanMessage

from chatbot.config import config as app_config
from chatbot.core.db import init_db
from chatbot.core.history import list_sessions, get_session_history, save_session_message
from chatbot.core.file_store import save_pdf_to_mongo
from chatbot.core.watcher import app_watcher
from chatbot.core.memory_profile import build_user_memory

from chatbot.services.vision_service import VisionService
from chatbot.router.dispatcher import build_rag_agent


# --- SERVICE CONTAINER ---
class AppContainer:
    def __init__(self):
        init_db()
        try:
            self.genai_client = genai.Client(api_key=app_config.GOOGLE_API_KEY)
            print("[App] GenAI Client Initialized.")
        except Exception as e:
            print(f"[App] GenAI Client Init Failed: {e}")
            self.genai_client = None

        # Init Vision
        self.vision_service = VisionService(self.genai_client)

        # Init Agent & Memory
        if self.genai_client:
            self.agent_executor, self.text_llm = build_rag_agent(self.genai_client, self.vision_service)
            self.memory_service = build_user_memory(self.text_llm)
        else:
            self.agent_executor = None
            self.memory_service = None

        # Start Watcher (Để xử lý file ngầm)
        app_watcher.start()


APP = AppContainer()


# --- HELPER FUNCTIONS ---
def handle_pdf_upload(pdf_path: str, session_id: str, user_id: str):
    """
    Chỉ lưu file vào DB/GridFS. Việc xử lý (Vectorize) do Watcher làm.
    """
    print(f"[main] Đang tải file lên hệ thống: {os.path.basename(pdf_path)}...")

    # 1. Lưu vào MongoDB (Status = 'uploaded')
    file_id = save_pdf_to_mongo(pdf_path, session_id, user_id)

    if not file_id:
        print("❌ [main] Lưu file thất bại.")
        return

    print("✅ [main] Đã lưu file. Hệ thống đang xử lý ngầm (Watcher)...")

    # (Optional) Chờ một chút để Watcher kịp bắt sự kiện và in log cho đẹp trên CLI
    # Trên thực tế (API) thì return luôn không cần chờ.
    time.sleep(1)


def handle_unified_query(query_text: str, image_path: str | None, user_id: str, session_id: str):
    print("--- Processing by Multi-Agent Graph ---")
    if not APP.agent_executor:
        print("Agent not ready.")
        return
    try:
        # 1. Lấy User Profile
        user_profile = APP.memory_service.get_profile(user_id)

        # 2. Input
        inputs = {
            "messages": [HumanMessage(content=query_text)],
            "user_info": user_profile or "Chưa có thông tin.",
            "image_path": image_path
        }

        # 3. Invoke Graph
        result = APP.agent_executor.invoke(inputs,
                                           config={"configurable": {"session_id": session_id, "user_id": user_id}})

        # 4. Output
        last_message = result["messages"][-1]
        full_response = last_message.content
        bot_name = last_message.name if hasattr(last_message, 'name') else 'Bot'

        print(f"\n🤖 {bot_name}: {full_response}\n")

        # 5. Save History & Update Profile
        save_session_message(session_id, user_id, query_text, full_response, image_gridfs_id=image_path)
        APP.memory_service.update_profile_background(user_id, query_text)

    except Exception as e:
        print(f"[main] Agent error: {e}")


# --- MAIN LOOP ---
def main():
    print("🤖 Chatbot Law (Unified Multi-Agent) sẵn sàng!")
    print("=" * 30)

    # Mock User ID (Trong thực tế lấy từ Authen)
    user_id = "6935267b0d228c9dbb5d0ecc"

    print("[1] Tạo session mới")
    print("[2] Tiếp tục session cũ")
    choice = input("Lựa chọn (1/2): ").strip()

    if choice == '2':
        sessions = list_sessions(limit=10, user_id=user_id)
        if not sessions:
            session_id = str(uuid.uuid4())
        else:
            for i, s in enumerate(sessions):
                print(f"  [{i + 1}] {s['session_id']} ({s['num_messages']} msgs)")
            try:
                s_choice = int(input("Chọn (0=Mới): ").strip())
                if 0 < s_choice <= len(sessions):
                    session_id = sessions[s_choice - 1]['session_id']
                else:
                    session_id = str(uuid.uuid4())
            except:
                session_id = str(uuid.uuid4())
    else:
        session_id = str(uuid.uuid4())

    print(f"\n🆔 Session ID: {session_id}")
    print("Gõ 'pdf' để tải file, 'exit' để thoát.\n")

    # Load lại lịch sử để Agent có context
    get_session_history(session_id, user_id)

    while True:
        user_input = input("\n👤 Bạn: ")
        if user_input.lower() == "exit": break

        if user_input.lower() == "pdf":
            path = input("📂 PDF Path: ").strip().replace('"', '')
            if os.path.exists(path):
                handle_pdf_upload(path, session_id, user_id)
            else:
                print("File không tồn tại.")
            continue

        img_path = input("🖼️ Ảnh Path (Enter để bỏ qua): ").strip().replace('"', '')
        if img_path == "":
            img_path = None
        elif not os.path.exists(img_path):
            print("⚠️ File ảnh không tồn tại. Tiếp tục chỉ với text.")
            img_path = None

        handle_unified_query(user_input, img_path, user_id, session_id)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        app_watcher.stop()
        print("\nGoodbye!")
    except Exception as e:
        app_watcher.stop()
        print(f"[main] Fatal Error: {e}")