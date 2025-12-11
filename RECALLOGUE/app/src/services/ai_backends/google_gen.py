import os
from typing import Optional
from google import generativeai as genai 
from google.generativeai import types
from app.src.services.ai_backends.schemas import *
from app.src.utils.colors import *


class GoogleGenAI:
    def __init__(self):
        """
        Initializes the GoogleGenAI client.
        It's recommended to set the GEMINI_API_KEY environment variable.
        The client will automatically use it.
        """
        
        api_key = os.getenv("GEMINI_API_KEY")

        if not api_key:
            raise ValueError("GEMINI_API_KEY environment variable not set.")
        
        # The client is configured upon import or via genai.configure()
        genai.configure(api_key=api_key) # pyright: ignore[reportPrivateImportUsage]
        
        # The model is instantiated, not just a name stored
        self.model_name = os.getenv("GEMINI_MODEL")
        if not self.model_name:
            raise ValueError("GEMINI_MODEL environment variable not set.")
        self.model = genai.GenerativeModel(self.model_name) # pyright: ignore[reportPrivateImportUsage]
        
    def get_model(self):
        return self.model_name
    
    def complete(self,
                 system_prompt: Optional[str] = None,
                 user: Optional[str] = None,
                 temperature: Optional[float] = 0.7,
                 max_tokens: Optional[int] = 1024,
                 payload = None) -> str:
        """
        Generates a response from the Gemini model.

        Args:
            system_prompt: The system instruction or context.
            user: The user's prompt (used if payload is not provided).
            temperature: The sampling temperature.
            max_tokens: The maximum number of tokens to generate.
            payload: A message history object.

        Returns:
            The generated text response from the model.
        """
        # Ensure system_prompt is a string, as it's used directly now.
        final_system_prompt = system_prompt or ""
        
        
        # Construct the conversation history
        contents = []
        if payload:
            for message in payload.messages:
                if message.role == "system":
                    # Override system prompt if present in the payload
                    final_system_prompt = message.content or "" 
                    continue
                role = "model" if message.role in ("assistant", "model", "agent") else "user"
                contents.append({'role': role, 'parts': [{'text': message.content}]})
        elif user:
            contents = [{'role': 'user', 'parts': [{'text': user}]}]
        else:
            raise ValueError("Either 'user' prompt or 'payload' must be provided.")

        generation_config = types.GenerationConfig(
            temperature=temperature,
            max_output_tokens=max_tokens,
            top_p=0.8,
            top_k=40,
        )
        
        print("Contents sent to Gemini model:")
        try:
            text = ""
            print(f"{INFO_COLOR}Response from {self.__class__.__name__}:{RESET}")
            
            # generate_content_stream is a method on the model object
            response_stream = self.model.generate_content(
                contents=contents,
                generation_config=generation_config,
                stream=True
            )
            
            for chunk in response_stream:
                # Access text safely, considering potential empty chunks
                chunk_text = getattr(chunk, 'text', '')
                print(chunk_text, end="")
                if chunk_text:
                    text += chunk_text

            with open("./storage/dev/response.txt", "a", encoding="utf-8") as f:
                f.write("\n" + "-" * 10)
                f.write(text)
                f.write("\n" + "-" * 10)
                
            print(f"\nResponse from Gemini model: {text}")
            return text
        except Exception as e:
            print(f"Error during Gemini model call: {e}")
            return f"An error occurred: {e}"