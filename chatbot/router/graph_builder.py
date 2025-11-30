from langgraph.graph import StateGraph, END
from langchain_core.messages import AIMessage

from chatbot.core.state import AgentState
from chatbot.router.supervisor import create_supervisor_node
from chatbot.llm.agent_react import create_agent_executor


# Helper tạo node worker chuyên môn (có Tools)
def create_worker_node(agent_executor, name):
    def worker_node(state: AgentState):
        last_message = state["messages"][-1]
        result = agent_executor.invoke({"question": last_message.content})
        return {
            "messages": [AIMessage(content=result["output"], name=name)]
        }

    return worker_node


# Helper tạo node worker xã giao (KHÔNG Tools - Chỉ LLM)
def create_general_node(llm, name="GeneralResponder"):
    def general_node(state: AgentState):
        last_message = state["messages"][-1]

        # System Prompt mới: Cực kỳ bảo thủ
        strict_system_prompt = (
            "Bạn là Chatbot Tra cứu Dữ liệu Nội bộ của CUSC.\n"
            "Nhiệm vụ: Chỉ trả lời các câu chào hỏi xã giao (Hello, Hi, Cảm ơn) hoặc giới thiệu bản thân.\n"
            "QUY TẮC:\n"
            "1. Nếu người dùng chào: Hãy chào lại thân thiện, ngắn gọn và mời họ đặt câu hỏi về quy trình/tài liệu.\n"
            "2. Nếu người dùng hỏi kiến thức bên ngoài (Code, Thời tiết, Lịch sử...): Hãy từ chối lịch sự. Nói rằng: 'Tôi là chatbot nội bộ CUSC, tôi chỉ hỗ trợ tra cứu các thông tin liên quan đến quy định và tài liệu của trung tâm.'\n"
            "3. KHÔNG tự bịa ra kiến thức không có trong ngữ cảnh."
        )

        response = llm.invoke([
            ("system", strict_system_prompt),
            last_message
        ])
        return {
            "messages": [AIMessage(content=response.content, name=name)]
        }

    return general_node


def create_vision_node(vision_service, name="VisionAnalyst"):
    def vision_node(state: AgentState):
        last_message = state["messages"][-1]
        image_path = state.get("image_path")

        # Guard clause: Nếu Supervisor lỡ điều hướng sai
        if not image_path:
            return {
                "messages": [
                    AIMessage(content="Lỗi: Yêu cầu phân tích ảnh nhưng không tìm thấy ảnh trong dữ liệu đầu vào.",
                              name=name)]
            }

        # Gọi Pure Service
        response_text = vision_service.analyze_image(
            query_text=last_message.content,
            image_path=image_path
        )
        return {
            "messages": [AIMessage(content=response_text, name=name)]
        }

    return vision_node


def build_multi_agent_graph(text_llm, tools_policy, tools_personal, vision_service):
    """
    Xây dựng đồ thị Multi-Agent với Adaptive Routing.
    """
    # Thêm GeneralResponder vào danh sách
    members = ["VisionAnalyst", "LawResearcher", "PersonalAnalyst", "GeneralResponder"]

    # 1. Supervisor
    supervisor_chain = create_supervisor_node(text_llm, members)

    # 2. Policy Agent (Nặng - Có Search)
    policy_agent = create_agent_executor(text_llm, tools_policy)
    law_node = create_worker_node(policy_agent, "LawResearcher")

    # 3. Personal Agent (Nặng - Có Search)
    personal_agent = create_agent_executor(text_llm, tools_personal)
    personal_node = create_worker_node(personal_agent, "PersonalAnalyst")

    # 4. General Agent (Nhẹ - No Search) --> MỚI
    general_node = create_general_node(text_llm, "GeneralResponder")

    # 5. Vision Agent
    vision_node = create_vision_node(vision_service, "VisionAnalyst")

    # 5. Khởi tạo Graph
    workflow = StateGraph(AgentState)

    workflow.add_node("Supervisor", supervisor_chain)
    workflow.add_node("LawResearcher", law_node)
    workflow.add_node("PersonalAnalyst", personal_node)
    workflow.add_node("GeneralResponder", general_node)
    workflow.add_node("VisionAnalyst", vision_node)

    # 6. Edges
    workflow.set_entry_point("Supervisor")

    workflow.add_conditional_edges(
        "Supervisor",
        lambda x: x["next"],
        {
            "LawResearcher": "LawResearcher",
            "PersonalAnalyst": "PersonalAnalyst",
            "GeneralResponder": "GeneralResponder",
            "VisionAnalyst": "VisionAnalyst",
            "FINISH": END
        }
    )

    # Tất cả làm xong thì END
    for member in members:
        workflow.add_edge(member, END)

    return workflow.compile()
