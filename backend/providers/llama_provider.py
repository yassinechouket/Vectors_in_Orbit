from .base import Provider
from typing import Optional, Any
from .exceptions import ProviderError
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))
from helpers.logger import get_logger
import requests
import asyncio
import re

logger = get_logger(__name__)   


class LlamaProvider(Provider):
    """
    Provider for Llama.
    """
    def __init__(
        self,
        model_name="llama-3.1-8b-instant"
    ):

        logger.info(f"Initializing LlamaProvider with model: {model_name}")  
        self.api_key = os.getenv("LLAMA_API_KEY")
        self.model_name = model_name
        self.url = "https://api.groq.com/openai/v1/chat/completions"

        logger.debug("Groq API key found")

        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        logger.debug("Groq API key found")
        logger.info("LlamaProvider initialized successfully")


    async def __call__(self, prompt: str, system: Optional[str] = None, **generation_args: Any) -> str: 

        logger.debug("Starting llama request")  
        
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
            logger.debug(f"Using system prompt (length: {len(system)} chars)")

        messages.append({"role": "user", "content": prompt})
        logger.debug(f"Sending prompt (length: {len(prompt)} chars)")
        
        payload = {
            "model": self.model_name,
            "messages": messages,
            **generation_args,     
        }

        max_retries = 10
        
        for attempt in range(max_retries):
            try:
                # Run blocking request in executor to avoid blocking the event loop
                loop = asyncio.get_running_loop()
                response = await loop.run_in_executor(
                    None, 
                    lambda: requests.post(self.url, headers=self.headers, json=payload)
                )

                if response.status_code == 200:
                    data = response.json()
                    content = data["choices"][0]["message"]["content"]
                    logger.debug(f"Response length: {len(content)} chars")
                    return content

                elif response.status_code == 429:
                    error_msg = response.text
                    logger.warning(f"Llama rate limit hit (attempt {attempt+1}/{max_retries})")
                    
                    # Try to parse wait time
                    wait_time = 10.0 # Default fallback
                    try:
                        match = re.search(r"Please try again in (\d+\.?\d*)s", error_msg)
                        if match:
                            wait_time = float(match.group(1)) + 2.0 # Add 2s buffer
                    except Exception:
                        pass
                    
                    logger.info(f"Waiting {wait_time:.2f}s before retry...")
                    await asyncio.sleep(wait_time)
                    continue
                
                else:
                    logger.error(f"Llama API returned {response.status_code}: {response.text}")
                    raise ProviderError(f"Llama API error: {response.text}")

            except Exception as e:
                # If we caught a ProviderError (from the else block above), re-raise it if max retries reached
                # But wait, the else block raises ProviderError, which is caught here.
                # We should probably check if it's a 429 error specifically or just generic error.
                # Actually, the 429 block uses 'continue', so it won't raise ProviderError.
                # The 'else' block raises ProviderError, which goes to 'except'.
                
                if attempt == max_retries - 1:
                    logger.error(f"Llama provider failed with error: {e}")
                    raise ProviderError(f"Llama error: {e}") from e
                
                # If it's not a rate limit error (which is handled in the if/elif), it's another error.
                # We can retry on other errors too, but maybe with a fixed delay.
                logger.warning(f"Request failed: {e}. Retrying in 5s...")
                await asyncio.sleep(5)
        
        raise ProviderError("Max retries exceeded")