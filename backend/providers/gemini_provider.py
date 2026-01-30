from .base import Provider
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage, SystemMessage
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))
from helpers.logger import get_logger
from typing import Optional, Any
from .exceptions import ProviderError  

logger = get_logger(__name__)   



class GeminiProvider(Provider):
    def __init__(
        self,
        model_name: str = "gemini-3-flash-preview",
        temperature: float = 0.0,
    ):
        logger.info(f"Initializing GeminiProvider with model: {model_name}")

        logger.debug("Google API key found")

        # Initialize ChatGoogleGenerativeAI
        self._client = ChatGoogleGenerativeAI(
            model=model_name,
            temperature=temperature,
            google_api_key=os.getenv("GOOGLE_GEN_AI_API_KEY"),
        )
        self.model = model_name
        logger.info("GeminiProvider initialized successfully")

    async def __call__(self, prompt: str, system: Optional[str] = None, **generation_args: Any) -> str:
        logger.debug("Starting Gemini LLM request")
        try:
            messages = []
            if system:
                messages.append(SystemMessage(content=system))
                logger.debug(f"Using system prompt (length: {len(system)} chars)")
            messages.append(HumanMessage(content=prompt))
            logger.debug(
                f"Sending request to Gemini (prompt length: {len(prompt)} chars)"
            )
            response= await self._client.ainvoke(messages,**generation_args)
            logger.debug("Gemini LLM request completed")
            return response.content
        except Exception as e:
            logger.error(f"Gemini provider failed with error: {e}")
            raise ProviderError(f"Gemini error: {e}") from e


        

        
