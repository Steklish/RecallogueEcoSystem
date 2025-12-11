
import spacy
from logger_config import get_logger



logger = get_logger(__name__)



class Prefetcher:
    
    def __init__(self) -> None:
        # Load Spacy
        try:
            nlp = spacy.load("ru_core_news_lg")
        except OSError:
            logger.warning("Spacy model 'ru_core_news_lg' not found. Please install it using: python -m spacy download ru_core_news_lg")
            raise ValueError("Spacy model 'ru_core_news_lg' is required but not found.")
        self.nlp = nlp

    def _detect_names(self, text: str) -> list[str]:
        """Detect potential entity names in the text using Spacy."""
        # Increase max length for large files
        self.nlp.max_length = max(len(text) + 1000, self.nlp.max_length)
        
        doc = self.nlp(text)
        # Extract entities relevant for context lookup (Person, Org, GPE, Loc)
        names = set([ent.text for ent in doc.ents if ent.label_ in ["PER", "ORG", "LOC", "GPE"]])
        return list(names)


    def get_entities(self, text: str) -> list:
        # Dummy implementation for prefetching entities
        return ["Entity1", "Entity2", "Entity3"]
    
    
    def get_topics(self, text: str) -> list:
        # Dummy implementation for prefetching topics
        return ["Topic1", "Topic2"]    
    