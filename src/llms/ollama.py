from langchain_ollama import ChatOllama
from .base import BaseLLMProvider

class OllamaProvider(BaseLLMProvider):
    def create_model(self, config: dict, **kwargs):
        return ChatOllama(
            model=config["MODEL"],
            base_url=config["BASE_URL"],
            temperature=config["TEMPERATURE"],
            reasoning_effort=config["REASONING_EFFORT"] if config.get("MODEL_TYPE") == "reasoning" else None,
        )
