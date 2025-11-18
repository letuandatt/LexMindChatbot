from langchain.agents.output_parsers.react_single_input import ReActSingleInputOutputParser
from langchain.schema import AgentFinish

class SafeReActOutputParser(ReActSingleInputOutputParser):
    def parse(self, text: str):
        text = text.strip()

        # 1. Nếu chứa Final Answer → trả luôn
        if "Final Answer:" in text:
            answer = text.split("Final Answer:", 1)[1].strip()
            return AgentFinish(
                return_values={"output": answer},
                log=text
            )

        # 2. Nếu có Action + Action Input đúng → dùng parser gốc
        try:
            return super().parse(text)
        except Exception:
            # 3. Fallback: không có Action → return Final Answer mặc định
            return AgentFinish(
                return_values={"output": text},
                log=text
            )
