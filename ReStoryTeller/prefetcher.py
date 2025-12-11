import spacy
from logger_config import get_logger
from sqlite_entity_manager import SQLiteEntityManager
from difflib import SequenceMatcher
from typing import List, Tuple, Dict, Any
from chroma_client import ChromaClient
logger = get_logger(__name__)



class Prefetcher:

    def __init__(self, db: SQLiteEntityManager, chroma : ChromaClient) -> None:
        # sqlite db for entity storage
        self.db = db
        # chroma client for topics retrieval
        self.chroma = chroma
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

    def _fuzzy_match(self, query: str, candidates: List[str], threshold: float = 0.6) -> List[Tuple[str, float]]:
        """
        Perform fuzzy matching between a query and a list of candidates.
        Includes both fuzzy matching and substring matching.

        :param query: The text to match against
        :param candidates: List of candidate strings to match
        :param threshold: Minimum similarity score (0-1) for a match to be considered
        :return: List of tuples (candidate, similarity_score) sorted by score descending
        """
        matches = []
        query_lower = query.lower().strip()

        for candidate in candidates:
            if not candidate:
                continue
            candidate_lower = candidate.lower().strip()

            # Check for substring match first (higher priority)
            if query_lower in candidate_lower or candidate_lower in query_lower:
                # For substring matches, assign a high similarity score
                # Length-normalized score to prefer exact matches
                length_factor = 1.0 - abs(len(query_lower) - len(candidate_lower)) / (max(len(query_lower), len(candidate_lower)) + 1)
                substring_similarity = 0.8 + 0.2 * length_factor  # High score for substring matches
                matches.append((candidate, substring_similarity))
            else:
                # Calculate similarity ratio for non-substring matches
                similarity = SequenceMatcher(None, query_lower, candidate_lower).ratio()
                if similarity >= threshold:
                    matches.append((candidate, similarity))

        # Sort by similarity score in descending order
        return sorted(matches, key=lambda x: x[1], reverse=True)

    def get_entities(self, text: str) -> List[Dict[str, Any]]:
        """
        Return all entities with their descriptions that are being found with fuzzy search in the database.

        :param text: Input text to search for entity matches
        :return: List of dictionaries containing entity names and descriptions that match the text
        """
        # Get all entities from the database
        all_entities = self.db.get_all_entities()

        # Extract the names from the entities for comparison
        entity_names = [entity[1] for entity in all_entities]  # entity[1] is the name

        # Detect names in the provided text
        detected_names = self._detect_names(text)

        # Perform fuzzy search for each detected name against all entities
        matched_entities = []
        for detected_name in detected_names:
            # Find similar entity names using fuzzy matching
            fuzzy_matches = self._fuzzy_match(detected_name, entity_names, threshold=0.6)

            # Add entities that have matches to the result
            for entity_name, similarity in fuzzy_matches:
                # Find the full entity details from the original list
                entity_details = next(
                    (entity for entity in all_entities if entity[1] == entity_name),
                    None
                )

                if entity_details:
                    id, name, description = entity_details
                    matched_entity = {
                        "name": name,
                        "description": description,
                        "similarity": similarity,
                        "detected_in_text": detected_name
                    }

                    # Avoid duplicates in the result
                    if not any(e["name"] == name for e in matched_entities):
                        matched_entities.append(matched_entity)

        logger.debug("Found %d matching entities for text", len(matched_entities))
        return matched_entities


    # Constant for number of topics to retrieve
    TOP_N_TOPICS = 5

    def get_topics(self, text: str) -> List[Dict[str, Any]]:
        """
        Retrieve the top N topics from ChromaDB based on the input text.

        :param text: Input text to search for relevant topics
        :return: List of topic dictionaries containing relevant text chunks and metadata
        """
        # Search for relevant chunks in ChromaDB
        try:
            search_results = self.chroma.search_chunks(
                query_text=text,
                top_k=self.TOP_N_TOPICS
            )

            # Extract the text content as topics
            topics = []
            for result in search_results:
                topic = {
                    "text": result["text"],
                    "metadata": result.get("metadata", {}),
                    "distance": result.get("distance", 0),
                    "id": result.get("id", "")
                }
                topics.append(topic)

            logger.debug("Retrieved %d topics for text query", len(topics))
            return topics
        except Exception as e:
            logger.error("Error retrieving topics from ChromaDB: %s", e)
            # Return empty list in case of error
            return []