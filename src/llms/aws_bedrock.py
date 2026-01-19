from langchain_aws import ChatBedrockConverse
from .base import BaseLLMProvider

class AWSBedrockProvider(BaseLLMProvider):
    def create_model(self, config: dict, **kwargs):
        return ChatBedrockConverse(
            aws_access_key_id=kwargs.get("aws_key"),
            aws_secret_access_key=kwargs.get("aws_secret"),
            model_id=config["MODEL"],
            region_name=config["AWS_REGION"],
            temperature=config["TEMPERATURE"],
            additional_model_request_fields={
                "reasoning_effort": config["REASONING_EFFORT"] if config.get("MODEL_TYPE") == "reasoning" else None
            },
        )
