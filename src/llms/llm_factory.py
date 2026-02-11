from .aws_bedrock import AWSBedrockProvider
from .google import GoogleProvider
from .groq import GroqProvider
from .huggingface import HuggingFaceProvider
from .llamacpp import LlamaCppProvider
from .nvidia import NVIDIAProvider
from .ollama import OllamaProvider
from .vllm import VLLMProvider


class LLMFactory:
    """Factory class to create LLM provider instances."""
    
    _providers = {
        "ollama": OllamaProvider,
        "vllm": VLLMProvider,
        "aws_bedrock": AWSBedrockProvider,
        "groq": GroqProvider,
        "nvidia": NVIDIAProvider,
        "google": GoogleProvider,
        "huggingface": HuggingFaceProvider,
        "llamacpp": LlamaCppProvider,
    }

    @classmethod
    def get_provider(cls, provider_type: str):
        provider_class = cls._providers.get(provider_type.lower())
        if not provider_class:
            raise ValueError(f"Unsupported LLM provider: {provider_type}")
        return provider_class()
