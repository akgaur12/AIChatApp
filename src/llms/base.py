from abc import ABC, abstractmethod

class BaseLLMProvider(ABC):
    """Abstract base class for LLM providers."""
    
    @abstractmethod
    def create_model(self, config: dict, **kwargs):
        """Creates and returns the LLM model instance."""
        pass
