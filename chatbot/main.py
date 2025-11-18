"""
Entry point for chatbot_v3 (CLI). Wires GenAI client, tools, agent, vision chain.
Minimal CLI for testing.
"""
import os
import uuid
import base64
import google.genai as genai

from chatbot.config import config as app_config
from chatbot.core.file_store import save_pdf_to_mongo, process_and_vectorize_pdf, get_session_file_stores
from chatbot.core.history import save_session_message, list_sessions, get_session_history
from chatbot.core.utils import image_to_base64
from chatbot.router.dispatcher import build_rag_agent
from chatbot.llm.llm_vision import create_vision_llm

import chatbot.tools.tool_search_policy as tool_policy
import chatbot.tools.tool_search_uploaded as tool_uploaded

# Init GenAI client
GLOBAL_GENAI_CLIENT = None
try:
    GLOBAL_GENAI_CLIENT = genai.Client(api_key=app_config.GOOGLE_API_KEY)
    print("[main] Google GenAI client initialized.")
except Exception as e:
    print(f"[main] Failed to init Google GenAI client: {e}")
    GLOBAL_GENAI_CLIENT = None

# inject client into tools
try:
    tool_policy.set_global_genai(GLOBAL_GENAI_CLIENT)
    tool_uploaded.set_global_genai(GLOBAL_GENAI_CLIENT)
except Exception:
    pass

# Build agent
RAG_AGENT_EXECUTOR, TEXT_LLM = build_rag_agent(GLOBAL_GENAI_CLIENT)

# Vision LLM (optional)
VISION_LLM = create_vision_llm()

def handle_pdf_upload(pdf_path: str, session_id: str, user_id: str):
    print(f"[main] Uploading file for session {session_id} ...")
    file_id = save_pdf_to_mongo(pdf_path, session_id, user_id)
    if not file_id:
        print("[main] save failed.")
        return
    # fetch doc to check id (simple)
    from core.db import DB_DOCUMENTS_COLLECTION
    try:
        doc = DB_DOCUMENTS_COLLECTION.find_one({"_id": __import__('bson').objectid.ObjectId(file_id)})
    except Exception:
        doc = None
    if doc and doc.get("status") == "processed":
        print("[main] File already processed.")
    else:
        process_and_vectorize_pdf(pdf_path, session_id, str(doc["_id"]), GLOBAL_GENAI_CLIENT)
        print("[main] Processed and created file store.")

def handle_text_query(query_text: str, user_id: str, session_id: str = "default_session"):
    print("--- Processing by RAG Agent ---")
    agent = RAG_AGENT_EXECUTOR
    if agent is None:
        print("Agent unavailable.")
        return
    try:
        res = agent.invoke({"question": query_text}, config={"configurable": {"session_id": session_id, "user_id": user_id}})
        full_response = res.get("output", "Không có phản hồi.") if isinstance(res, dict) else str(res)
        print(f"\nAnswer:\n{full_response}\n")
        save_session_message(session_id, user_id, query_text, full_response)
    except Exception as e:
        print(f"[main] Agent error: {e}")

def handle_multimodal_query(query_text: str, image_path: str, user_id: str, session_id: str):
    if not os.path.exists(image_path):
        print("Image not found.")
        return
    image_b64 = image_to_base64(image_path)
    if not image_b64:
        print("Image processing failed.")
        return
    # Basic vision pipeline (use raw genai SDK for image)
    if GLOBAL_GENAI_CLIENT and app_config.VISION_MODEL_NAME:
        try:
            from google.genai import types
            response = GLOBAL_GENAI_CLIENT.models.generate_content(
                model=app_config.VISION_MODEL_NAME,
                contents=[
                    types.Part(text=query_text),
                    types.Part(inline_data=types.Blob(mime_type="image/jpeg", data=base64.b64decode(image_b64)))
                ],
            )
            text = "".join(p.text for p in response.candidates[0].content.parts if hasattr(p, "text"))
            print(text)
            save_session_message(session_id, user_id, query_text, text)
        except Exception as e:
            print(f"Vision processing error: {e}")
    else:
        print("Vision LLM not available.")

def main():
    print("🤖 Chatbot CUSC (Agent + Google File Search) sẵn sàng!")
    print("=" * 30)
    print("[1] Tạo session mới")
    print("[2] Tiếp tục session cũ")

    user_id = "6915f6a4d74b46caa1d4d0b2"
    choice = input("Lựa chọn của bạn (1 hoặc 2): ").strip()

    if choice == '2':
        sessions = list_sessions(limit=10, user_id=user_id)
        if not sessions:
            session_id = str(uuid.uuid4())
        else:
            for i, s in enumerate(sessions):
                print(f"  [{i + 1}] {s['session_id']} ({s['num_messages']} tin nhắn, cập nhật: {s['updated_at']})")
            try:
                s_choice = int(input("Chọn session (0 để tạo mới): ").strip())
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

    get_session_history(session_id, user_id)  # Pre-load history

    while True:
        user_input = input("\n👤 Bạn: ")
        if user_input.lower() == "exit":
            break

        if user_input.lower() == "pdf":
            path = input("📂 PDF Path: ").strip().replace('"', '')
            if os.path.exists(path):
                handle_pdf_upload(path, session_id, user_id)
            else:
                print("File không tồn tại.")
            continue

        img_path = input("🖼️ Ảnh Path (Enter để bỏ qua): ").strip().replace('"', '')
        if img_path and os.path.exists(img_path):
            handle_multimodal_query(user_input, img_path, user_id, session_id)
        else:
            handle_text_query(user_input, user_id, session_id)


if __name__ == "__main__":
    main()