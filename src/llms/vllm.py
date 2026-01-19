from langchain_openai import ChatOpenAI
from .base import BaseLLMProvider

class VLLMProvider(BaseLLMProvider):
    def create_model(self, config: dict, **kwargs):
        return ChatOpenAI(
            model_name=config["MODEL"],
            openai_api_key=config["API_KEY"],
            openai_api_base=config["BASE_URL"],
            temperature=config["TEMPERATURE"],
            reasoning_effort=config["REASONING_EFFORT"] if config.get("MODEL_TYPE") == "reasoning" else None,
        )
