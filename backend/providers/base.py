"""Base provider class for LLM providers."""
from abc import ABC, abstractmethod
from typing import Optional, Any


class Provider(ABC):
    """Base class for all LLM providers."""
    
    @abstractmethod
    async def __call__(
        self, 
        prompt: str, 
        system: Optional[str] = None, 
        **generation_args: Any
    ) -> str:
        """
        Generate a response from the LLM.
        
        Args:
            prompt: The user prompt/query
            system: Optional system prompt for context
            **generation_args: Additional generation parameters (temperature, max_tokens, etc.)
            
        Returns:
            Generated text response from the LLM
        """
        pass
