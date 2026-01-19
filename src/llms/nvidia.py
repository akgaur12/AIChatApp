from langchain_nvidia_ai_endpoints import ChatNVIDIA
from .base import BaseLLMProvider

class NVIDIAProvider(BaseLLMProvider):
    def create_model(self, config: dict, **kwargs):
        return ChatNVIDIA(
            api_key=kwargs.get("api_key"),
            model=config["MODEL"],
            temperature=config["TEMPERATURE"],
        )
