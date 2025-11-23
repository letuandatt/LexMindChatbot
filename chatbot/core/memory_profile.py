from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from chatbot.core.db import get_mongo_collection

# Prompt trích xuất thông tin cá nhân
PROFILE_EXTRACT_PROMPT = """Bạn là một chuyên gia ghi nhớ thông tin người dùng.
Nhiệm vụ: Đọc tin nhắn mới nhất của người dùng và cập nhật hồ sơ của họ.

HỒ SƠ HIỆN TẠI:
{current_profile}

TIN NHẮN MỚI:
{user_message}

HÃY TRÍCH XUẤT CÁC THÔNG TIN: Tên, Chức vụ, Phòng ban, Sở thích, Dự án đang làm, hoặc phong cách làm việc.
- Nếu tin nhắn có thông tin mới/thay đổi: Hãy viết lại bản tóm tắt hồ sơ người dùng (ngắn gọn, gạch đầu dòng).
- Nếu tin nhắn không có thông tin cá nhân (chỉ hỏi xã giao hoặc hỏi kiến thức): Trả về "SKIP".

KẾT QUẢ (Chỉ trả về nội dung hồ sơ mới hoặc "SKIP"):
"""


class UserProfileMemory:
    def __init__(self, llm):
        self.llm = llm
        # Tên collection lưu profile user
        self.collection = get_mongo_collection("users")
        self.chain = (
                PromptTemplate.from_template(PROFILE_EXTRACT_PROMPT)
                | self.llm
                | StrOutputParser()
        )

    def get_profile(self, user_id: str) -> str:
        """Lấy hồ sơ hiện tại từ DB"""
        if self.collection is None:
            return ""
        try:
            user_doc = self.collection.find_one({"user_id": user_id})
            return user_doc.get("profile_summary", "") if user_doc else ""
        except Exception:
            return ""

    def update_profile_background(self, user_id: str, user_message: str):
        """
        Hàm này phân tích tin nhắn để cập nhật profile user.
        """
        if self.collection is None:
            return

        current_profile = self.get_profile(user_id)

        try:
            # Gọi LLM để xem có gì cần update không
            result = self.chain.invoke({
                "current_profile": current_profile or "(Chưa có thông tin)",
                "user_message": user_message
            })

            if result.strip() == "SKIP":
                return  # Không có gì mới

            # Lưu update vào DB
            self.collection.update_one(
                {"user_id": user_id},
                {"$set": {"profile_summary": result.strip()}},
                upsert=True
            )
            print(f"🧠 [Memory] Đã cập nhật hồ sơ user {user_id}")

        except Exception as e:
            print(f"⚠️ [Memory] Lỗi cập nhật profile: {e}")


# Factory function để inject vào AppContainer
def build_user_memory(llm):
    return UserProfileMemory(llm)
