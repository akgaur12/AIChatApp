from langchain_huggingface import ChatHuggingFace, HuggingFaceEndpoint
from .base import BaseLLMProvider

class HuggingFaceProvider(BaseLLMProvider):
    def create_model(self, config: dict, **kwargs):
        llm = HuggingFaceEndpoint(
            huggingfacehub_api_token=kwargs.get("api_key"),
            repo_id=config["MODEL"],
            task=config["MODEL_TYPE"],
            max_new_tokens=config["MAX_TOKENS"],
            do_sample=False,
            repetition_penalty=1.03,
            provider=config["PROVIDER"],
            streaming=config["STREAMING"],
        )
        return ChatHuggingFace(llm=llm)
