from langchain_google_genai import ChatGoogleGenerativeAI
from chatbot.config import config as app_config

def create_text_llm():
    """
    Returns a LangChain wrapper for Google GenAI text model.
    """
    try:
        return ChatGoogleGenerativeAI(
            model=app_config.TEXT_MODEL_NAME,
            temperature=0.1,
            google_api_key=app_config.GOOGLE_API_KEY  # Explicit API key
        )
    except Exception as e:
        print(f"[llm.llm_text] Error init TEXT_LLM: {e}")
        return None