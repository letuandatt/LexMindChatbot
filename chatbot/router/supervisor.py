from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.output_parsers.openai_tools import JsonOutputKeyToolsParser


def create_supervisor_node(llm, members: list[str]):
    system_prompt = (
        "Bạn là Supervisor của chatbot nội bộ CUSC. Nhiệm vụ là định tuyến chính xác.\n"
        "Các thành viên (Workers): {members}.\n\n"
        "QUY TẮC ĐIỀU PHỐI (NGHIÊM NGẶT):\n"
        "1. 'VisionAnalyst': BẮT BUỘC CHỌN nếu input có chứa HÌNH ẢNH (Image) hoặc người dùng yêu cầu phân tích ảnh.\n"
        "2. 'PolicyResearcher': Dùng cho câu hỏi chuyên môn, quy định, quy trình, thủ tục, ISO, hoặc kiến thức công việc.\n"
        "3. 'PersonalAnalyst': Dùng cho câu hỏi về File upload hoặc lịch sử chat.\n"
        "4. 'GeneralResponder': CHỈ DÙNG cho các câu CHÀO HỎI XÃ GIAO ('Xin chào', 'Cảm ơn', 'Bye') hoặc hỏi về DANH TÍNH BOT ('Bạn là ai').\n"
        "   - CẢNH BÁO: Nếu người dùng hỏi kiến thức bên ngoài (Ví dụ: 'Thủ đô Paris?', 'Cách nấu ăn?', 'Viết code Python'), HÃY CHỌN 'PolicyResearcher' (để hệ thống tìm trong tài liệu nội bộ, nếu không thấy sẽ báo không có).\n"
        "   - TUYỆT ĐỐI KHÔNG dùng GeneralResponder để trả lời kiến thức không liên quan CUSC.\n\n"
        "Chọn 'FINISH' nếu đã xong."
    )

    options = ["FINISH"] + members

    # Schema cho function calling
    function_def = {
        "name": "route",
        "description": "Select the next role.",
        "parameters": {
            "type": "object",
            "properties": {
                "next": {
                    "title": "Next Role",
                    "anyOf": [
                        {"enum": options},
                    ],
                }
            },
            "required": ["next"],
        },
    }

    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        MessagesPlaceholder(variable_name="messages"),
        ("human", "Dựa vào nội dung trên (và xem có ảnh không), ai nên hành động tiếp theo? Chọn MỘT trong: {options}"),
    ]).partial(options=str(options), members=", ".join(members))

    # Supervisor chain
    supervisor_chain = (
        prompt
        | llm.bind_tools(tools=[function_def], tool_choice="route")
        | JsonOutputKeyToolsParser(key_name="route", first_tool_only=True)
    )

    return supervisor_chain
