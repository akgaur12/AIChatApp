from langchain_groq import ChatGroq
from .base import BaseLLMProvider

class GroqProvider(BaseLLMProvider):
    def create_model(self, config: dict, **kwargs):
        return ChatGroq(
            api_key=kwargs.get("api_key"),
            model=config["MODEL"],
            temperature=config["TEMPERATURE"],
            reasoning_effort=config["REASONING_EFFORT"] if config.get("MODEL_TYPE") == "reasoning" else None,
        )
