from datetime import datetime
import os
import re
from typing import List, Tuple, Dict, Any, Optional
import spacy
from schemas import AIKnowledgeGraph, Article
from difflib import SequenceMatcher

from logger_config import get_logger
from generator import Generator
from chroma_client import ChromaClient
from sqlite_entity_manager import SQLiteEntityManager
from neo4j_manager import Neo4jGraphManager

logger = get_logger(__name__)



class Processor:

    def __init__(self, db: SQLiteEntityManager, chroma : ChromaClient, generator : Generator, neo : Neo4jGraphManager) -> None:
        # sqlite db for entity storage
        self.db = db
        # chroma client for topics retrieval
        self.chroma = chroma
        # llm generator to generate pydantic-defined objects
        self.generator = generator
        # neo4j manager for graph storage
        self.neo = neo
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

    def add_entity(self, name: str, description: str) -> bool:
        """
        Add an entity to the SQLite database.

        :param name: Name of the entity
        :param description: Description of the entity
        :return: True if the entity was added successfully, False otherwise
        """
        try:
            success = self.db.insert_entity(name, description)
            if success:
                logger.debug("Added entity to database: %s", name)
            else:
                logger.warning("Failed to add entity to database: %s", name)
            return success
        except Exception as e:
            logger.error("Error adding entity to database: %s", e)
            return False

    def add_topic(self, text_chunk: str, metadata: Optional[Dict[str, Any]] = None, chunk_id: Optional[str] = None) -> bool: # type: ignore
        """
        Add a topic (text chunk) to the ChromaDB.

        :param text_chunk: The text content to store as a topic
        :param metadata: Optional metadata dictionary for the topic
        :param chunk_id: Optional ID for the topic chunk, auto-generated if not provided
        :return: True if the topic was added successfully, False otherwise
        """
        try:
            # Generate embedding for the text chunk using the chroma client's embedding client
            vector = self.chroma.embedding_client.embed_text(text_chunk)

            if not vector:
                logger.error("Failed to generate embedding for text chunk: %s", text_chunk[:50] + "...")
                return False

            # Use the ChromaClient's method to store a single chunk with vector
            result_chunk_id = self.chroma.store_chunk_with_vector(
                text_chunk=text_chunk,
                vector=vector,
                metadata=metadata, # type: ignore
                chunk_id=chunk_id # type: ignore
            )

            if result_chunk_id:
                logger.debug("Added topic to ChromaDB with ID: %s", result_chunk_id)
                return True
            else:
                logger.warning("Failed to add topic to ChromaDB")
                return False
        except Exception as e:
            logger.error("Error adding topic to ChromaDB: %s", e)
            return False
        
        
        
    def get_KG_from_text(self, text, entities_with_description=None, topics_suggestions=None) -> AIKnowledgeGraph:
        
        # Формируем контекст из JSON или строк
        candidates_ent_str = str(entities_with_description) if entities_with_description else "Список пуст."
        candidates_topic_str = str(topics_suggestions) if topics_suggestions else "Список пуст."


        instructions = f"""
        Ты — ведущий аналитик данных для графовой базы знаний (Knowledge Graph Engineer).
        Твоя задача — преобразовать новостную статью в структурированные данные, связав их с уже существующей базой знаний.

        === ВХОДНЫЕ ДАННЫЕ ===
        
        1. ТЕКСТ СТАТЬИ:
        "{text}"

        2. КАНДИДАТЫ (СУЩЕСТВУЮЩИЕ ТЕМЫ):
        {candidates_topic_str}
        *Это список активных сюжетов. Если статья развивает один из них, ты ОБЯЗАН привязать её к нему.*

        3. КАНДИДАТЫ (ИЗВЕСТНЫЕ СУЩНОСТИ):
        {candidates_ent_str}
        *Это список людей/компаний, которые уже есть в графе.*

        === АЛГОРИТМ РАБОТЫ ===

        ШАГ 1: ОПРЕДЕЛЕНИЕ ТЕМЫ (SAGA)
        - Проанализируй, относится ли статья к одной из "Существующих тем".
        - Если ДА: Верни её так, как она представлена.
        - Если НЕТ: Придумай новое название. Оно должно быть конкретным СОБЫТИЕМ (например, "Банкротство банка SVB", а не просто "Банки").

        ШАГ 2: ИЗВЛЕЧЕНИЕ СУЩНОСТЕЙ (ENTITY MATCHING)
        - Найди ключевых действующих лиц.
        - Для каждого найденного проверь список "Известных сущностей".
        - Если есть совпадение (даже нечеткое, например "Маск" -> "Илон Маск"):
        -> Используй его из списка кандидатов (в виде, как он представлен в списке).
        - Если совпадения нет:
        -> Создай новую сущность.
        - ВАЖНО: Не создавай сущности для общих понятий ("граждане", "полиция", "эксперты"). Только конкретные имена.

        ШАГ 3: СОЗДАНИЕ СВЯЗЕЙ
        - Связывай сущности действиями.
        - Если связь упоминает дату (вчера  , 10 декабря), укажи её в поле date.
        - Не сохраняй "Должности" (Role) внутри человека. Создай узел Role (например, "CEO") и свяжи: Person -> HELD_POSITION -> Role.

        === СТРОГИЕ ПРАВИЛА ===
        1. Язык полей 'context' и 'description': Русский.
        2. Язык полей 'label' и 'type': Английский (Person, LOCATED_IN).
        3. Даты: формат YYYY-MM-DD.
        4. Topic Name: Запрещено использовать общие слова ("Политика", "Мир"). Только конкретные сюжеты.
        """
        # LLM generates pydantic schema
        res = self.generator.generate_one_shot(
            pydantic_model=AIKnowledgeGraph,
            language="Russian",
            prompt=instructions + instructions
        )
        return res
    
    
    def _create_article_from_file(self, filename: str, text: str) -> Article:
        """
        Create an Article object from a file.

        :param filename: Name of the file (used as title)
        :param text: Full article text
        :return: Article object
        """
        
        def extract_date_from_path(filepath: str) -> str:
            # Extract the directory containing the date (e.g., "01.02.2011")
            parts = filepath.split(os.sep)
            date_pattern = re.compile(r'\b(\d{2}\.\d{2}\.\d{4})\b')
            
            for part in parts:
                match = date_pattern.search(part)
                if match:
                    date_str = match.group(1)
                    # Convert to YYYY-MM-DD
                    date_obj = datetime.strptime(date_str, "%d.%m.%Y")
                    return date_obj.strftime("%Y-%m-%d")
            
            raise ValueError("No date found in the file path.")
        
        return self._create_article(
            text=text,
            title=filename.split('.')[0],
            date=extract_date_from_path(filename)
        )
            
            
    def _create_article(self, text: str, title: str, date : str) -> Article:
        """
        Create an Article object from text and title.

        :param text: Full article text
        :param title: Article title
        :return: Article object
        """
        
        article = Article(
            name=title,
            text=text,
            date=date
        )
        return article
    
    
    def process_file(self, filename):
        clean_filename = filename.strip()
        if not os.path.exists(clean_filename):
            logger.error(f"File not found: {clean_filename}")
            return
        try:
            with open(clean_filename, "r", encoding="utf-8") as f:
                text = f.read()
            kg = self.get_KG_from_text(text)
            article = self._create_article_from_file(clean_filename, text)
            #generating queries
            queries = self.neo.generate_cypher_queries(
                article=article, 
                graph_data=kg
            )
            
            
            logger.info(f"Processed file {clean_filename}: {kg}")
            return kg
        except Exception as e:
            logger.error(f"Error processing file {clean_filename}: {e}", exc_info=True)
            return
        
    