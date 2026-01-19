from langchain_google_genai import ChatGoogleGenerativeAI
from .base import BaseLLMProvider

class GoogleProvider(BaseLLMProvider):
    def create_model(self, config: dict, **kwargs):
        return ChatGoogleGenerativeAI(
            api_key=kwargs.get("api_key"),
            model=config["MODEL"],
            temperature=config["TEMPERATURE"],
            max_retries=config["MAX_RETRIES"]
        )
