"""
Build and return the RAG agent executor and LLM objects.
This module wires tools -> llm -> agent.
"""
from chatbot.tools import set_genai_policy, set_genai_uploaded
from chatbot.tools import tool_search_general_policy, tool_search_uploaded_file, tool_list_uploaded_files
from chatbot.llm.llm_text import create_text_llm
from chatbot.llm.agent_react import create_agent_executor

def build_rag_agent(genai_client):
    # inject genai client into tools that need it
    try:
        set_genai_policy(genai_client)
    except Exception:
        pass
    try:
        set_genai_uploaded(genai_client)
    except Exception:
        pass

    text_llm = create_text_llm()
    tools = [tool_search_general_policy, tool_search_uploaded_file, tool_list_uploaded_files]
    agent = create_agent_executor(text_llm, tools)
    return agent, text_llm