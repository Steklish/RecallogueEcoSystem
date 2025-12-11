import os
import requests
from typing import List
from logger_config import get_logger

logger = get_logger(__name__)

class EmbeddingClient:
    def __init__(self, base: str = os.getenv("LLAMACPP_EMBED_BASE","http://localhost:8080")):
        """
        Initializes the EmbeddingClient.

        :param base: The base URL of the llama.cpp server.
        """
        self.base = base
        logger.info("Embedding Server instantiated successfully at %s", self.base)
    
    def embed_text(self, text: str) -> List[float]:
        """
        Generates an embedding for the given text.

        :param text: The text to embed.
        :return: A list of floats representing the embedding.
        """
        logger.debug("Embedding text: %s...", text[:30])  # Debug print
        try:
            response = requests.post(
                f"{self.base}/embedding",
                json={"content": text},
                headers={"Content-Type": "application/json"},
            )
            response.raise_for_status()
            
            data = response.json()
            try:
                # The server returns a list containing a dictionary, 
                # with the embedding nested inside a list.
                return data[0]['embedding'][0]
            except (IndexError, KeyError, TypeError) as e:
                logger.error("Failed to parse embedding from server response: %s", e)
                logger.debug("Received data: %s", data)
                return []

        except requests.exceptions.RequestException as e:
            logger.error("An error occurred while communicating with the embedding server: %s", e)
            return []
        except Exception as e:
            logger.error("An unexpected error occurred: %s", e)
            return []

    def embed_texts(self, texts: List[str], batch_size: int = 20) -> List[List[float]]:
        """
        Generates embeddings for a list of texts in batches.

        :param texts: The list of texts to embed.
        :param batch_size: The number of texts to process in each batch.
        :return: A list of lists of floats representing the embeddings.
        """
        logger.debug("Embedding texts: %s...", [text[:30] + '... len ->' + str(len(text)) for text in texts[:3]])  # Debug print
        all_embeddings = []
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            
            try:
                response = requests.post(
                    f"{self.base}/embedding",
                    json={"content": batch},
                    headers={"Content-Type": "application/json"},
                )
                response.raise_for_status()
                
                data = response.json()
                
                # Assuming the server returns a list of embedding results for a batch
                batch_embeddings = [item['embedding'][0] for item in data]
                all_embeddings.extend(batch_embeddings)

            except requests.exceptions.RequestException as e:
                logger.error("An error occurred while communicating with the embedding server: %s", e)
                # Pad with empty embeddings for the failed batch
                all_embeddings.extend([[]] * len(batch))
            except (KeyError, TypeError) as e:
                logger.error("Failed to parse embeddings from server response: %s", e)
                logger.debug("Received data: %s", data)
                all_embeddings.extend([[]] * len(batch))
        return all_embeddings

    def _get_model_from_server(self):
        try:
            response = requests.get(f"{self.base}/models")
            logger.debug("Model response: %s", response)
            response.raise_for_status()
            models = response.json().get("data", [])
            if models:
                return models[0]["id"][models[0]["id"].rfind("\\") + 1:]
            return "No models found"
        except requests.exceptions.RequestException as e:
            logger.error("Error fetching models from server: %s", e)
            return "Not available"
    
if __name__ == "__main__":
    # Example usage
    client = EmbeddingClient()
    
    # --- Text to embed ---
    text_to_embed = "This is a test sentence for the embedding client."
    
    logger.info("Embedding the text: '%s'", text_to_embed)

    # --- Generate embedding ---
    embedding = client.embed_text(text_to_embed)

    # --- Log results ---
    if embedding:
        logger.info("Successfully generated embedding of dimension: %d", len(embedding))
        logger.info("Embedding vector (first 10 values): %s", embedding[:10])
    else:
        logger.warning("Failed to generate embedding.")