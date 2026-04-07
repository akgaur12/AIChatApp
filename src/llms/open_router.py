from langchain_openrouter import ChatOpenRouter

from .base import BaseLLMProvider


class OpenRouterProvider(BaseLLMProvider):
    def create_model(self, config: dict, **kwargs):
        reasoning_config = None

        if config.get("MODEL_TYPE") == "reasoning":
            effort = config.get("REASONING_EFFORT", "medium")

        reasoning_config = {
            "effort": effort,
            "max_tokens": 1000, # Directly specifies the maximum number of tokens to use for reasoning
            "enabled": False,   # if True, Enables reasoning at the “medium” effort level with no exclusions.
            "exclude": True     # if True, the model will still use reasoning, but it won’t be returned in the response
        }

        return ChatOpenRouter(
            openrouter_api_key=kwargs.get("api_key"),
            model=config["MODEL"],
            temperature=config["TEMPERATURE"],
            max_tokens=config["MAX_TOKENS"],
            max_retries=config["MAX_RETRIES"],
            reasoning=reasoning_config,
        )