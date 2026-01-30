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


class DeepSeekProvider(Provider):
    """
    Provider for DeepSeek API (OpenAI-compatible).
    """
    def __init__(
        self,
        model_name="deepseek-chat"
    ):
        logger.info(f"Initializing DeepSeekProvider with model: {model_name}")
        self.api_key = os.getenv("DEEPSEEK_API_KEY")
        
        if not self.api_key:
            raise ProviderError("DEEPSEEK_API_KEY environment variable not set")
        
        # Remove "Bearer " prefix if it exists
        if self.api_key.startswith("Bearer "):
            self.api_key = self.api_key.replace("Bearer ", "")
            logger.debug("Removed 'Bearer ' prefix from API key")
        
        self.model_name = model_name
        self.url = "https://api.deepseek.com/v1/chat/completions"

        logger.debug("DeepSeek API key found")

        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        logger.info("DeepSeekProvider initialized successfully")

    async def __call__(self, prompt: str, system: Optional[str] = None, **generation_args: Any) -> str:
        logger.debug("Starting DeepSeek request")
        
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
                    logger.warning(f"DeepSeek rate limit hit (attempt {attempt+1}/{max_retries})")
                    
                    # Try to parse wait time
                    wait_time = 10.0  # Default fallback
                    try:
                        match = re.search(r"Please try again in (\d+\.?\d*)s", error_msg)
                        if match:
                            wait_time = float(match.group(1)) + 2.0  # Add 2s buffer
                    except Exception:
                        pass
                    
                    logger.info(f"Waiting {wait_time:.2f}s before retry...")
                    await asyncio.sleep(wait_time)
                    continue
                
                else:
                    logger.error(f"DeepSeek API returned {response.status_code}: {response.text}")
                    raise ProviderError(f"DeepSeek API error: {response.text}")

            except ProviderError:
                # Re-raise ProviderError immediately
                raise
            except Exception as e:
                if attempt == max_retries - 1:
                    logger.error(f"DeepSeek provider failed with error: {e}")
                    raise ProviderError(f"DeepSeek error: {e}") from e
                
                logger.warning(f"Request failed: {e}. Retrying in 5s...")
                await asyncio.sleep(5)
        
        raise ProviderError("Max retries exceeded")
