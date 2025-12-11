import os
import json
import logging
import requests
from typing import Optional, List, Dict, Any, Union
from dotenv import load_dotenv

from logger_config import get_logger

logger = get_logger(__name__)

load_dotenv(override=True)

class OpenRouterGenAI:
    def __init__(self, api_key: Optional[str] = None, model_name: Optional[str] = None):
        """
        Initializes the OpenRouter client.
        
        Args:
            api_key: OpenRouter API Token. Defaults to env var OR_TOKEN.
            model_name: Model identifier (e.g., 'qwen/qwen-2-7b-instruct'). Defaults to env var OR_MODEL.
        """
        self.api_key = api_key or os.getenv("OR_TOKEN")
        self.model_name = model_name or os.getenv("OR_MODEL")
        self.base_url = "https://openrouter.ai/api/v1/chat/completions"

        if not self.api_key:
            raise ValueError("API Key is missing. Set OR_TOKEN env var or pass it to the constructor.")
        
        if not self.model_name:
            logger.warning("No model name provided. Ensure OR_MODEL is set or pass model_name.")

    def get_model(self) -> str:
        return self.model_name if self.model_name else "model_name is not accessible"
    
    def complete(self,
                 user: Optional[str] = None,
                 system_prompt: Optional[str] = None,
                 payload: Any = None,
                 temperature: float = 0.7,
                 max_tokens: int = 1024) -> str:
        """
        Generates a response from the model via OpenRouter API.

        Args:
            user: The current user prompt.
            system_prompt: The system instruction (overrides payload system message if provided).
            payload: A message history object (must have .messages attribute).
            temperature: The sampling temperature.
            max_tokens: The maximum number of tokens to generate.

        Returns:
            The generated text response.
        
        Raises:
            requests.exceptions.RequestException: If the API call fails.
        """
        messages: List[Dict[str, str]] = []

        # 1. Handle System Prompt
        # If an explicit system_prompt is passed, it takes priority as the first message
        if system_prompt:
            messages.append({'role': 'system', 'content': system_prompt})

        # 2. Handle Payload (History)
        if payload and hasattr(payload, 'messages'):
            for message in payload.messages:
                # Map roles to standard OpenAI API roles
                role = message.role
                if role in ["model", "agent"]:
                    role = "assistant"
                
                # If we already added an explicit system prompt, skip system messages in history
                # to avoid duplicates or confusion, otherwise include them.
                if role == "system" and system_prompt:
                    continue
                
                messages.append({'role': role, 'content': message.content})

        # 3. Handle User Input
        # We append the user input to the end of the history
        if user:
            messages.append({'role': 'user', 'content': user})
            

        if not messages:
            raise ValueError("No messages provided. Supply 'user', 'payload', or 'system_prompt'.")

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
            # "HTTP-Referer": "http://localhost", # Optional: Required by OpenRouter for ranking
            # "X-Title": "My App", # Optional: Required by OpenRouter for ranking
        }

        data = {
            "model": self.model_name,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

        # Debug log (only shows if logging level is DEBUG)
        logger.debug(f"Payload sending to OpenRouter: {json.dumps(messages, indent=2, ensure_ascii=False)}")
        
        try:
            response = requests.post(self.base_url, headers=headers, json=data)
            response.raise_for_status()
            
            result = response.json()
            
            # OpenRouter specific: Check for non-standard error structures
            if 'error' in result:
                raise requests.exceptions.HTTPError(f"OpenRouter Error: {result['error']}")

            content = result['choices'][0]['message']['content']
            return content

        except requests.exceptions.RequestException as e:
            logger.error(f"API Request failed: {e}")
            if hasattr(e, 'response') and e.response is not None:
                logger.error(f"Status Code: {e.response.status_code}")
                logger.error(f"Response Body: {e.response.text}")
            
            # Re-raise the exception so the calling application knows it failed
            raise e
        except (KeyError, IndexError) as e:
            logger.error(f"Malformed response format: {e}")
            raise ValueError("Unexpected response format from OpenRouter") from e

# Example Usage
if __name__ == "__main__":
    try:
        # You can init with args or rely on .env
        ai = OpenRouterGenAI() 
        
        # Simple test
        response = ai.complete(
            system_prompt="You are a helpful coding assistant.",
            user="Write a hello world in Python."
        )
        logger.info(f"\nResponse:\n{response}")
        
    except Exception as err:
        logger.error(f"Failed to generate: {err}")