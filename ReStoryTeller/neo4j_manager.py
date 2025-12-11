import hashlib
import re
from typing import Any, List, Tuple
from neo4j import GraphDatabase
import logging

from pyparsing import Dict
from schemas import AIKnowledgeGraph, Article

class Neo4jGraphManager:
    def __init__(self, uri: str, auth: tuple):
        self.driver = GraphDatabase.driver(uri, auth=auth)
        self.logger = logging.getLogger("Neo4jManager")  
        self.create_indexes()

    def close(self):
        self.driver.close()

    def _sanitize(self, val: Any) -> str:
        if isinstance(val, str):
            safe_str = val.replace("'", "\\'")
            safe_str.lower()
            return f"'{safe_str}'"
        elif isinstance(val, bool):
            return "true" if val else "false"
        elif val is None:
            return "null"
        else:
            return str(val).replace("'", "\\'")


    def _generate_article_id(self, article: Article) -> str:
        """Генерирует уникальный ID для статьи на основе заголовка и даты."""
        raw_str = f"{article.name}_{article.date}"
        return hashlib.md5(raw_str.encode()).hexdigest()


    def _sanitize_for_cypher(self, text: str) -> str:
        """
        Очищает строку для использования в качестве типа связи или лейбла.
        Заменяет пробелы на _, убирает спецсимволы, приводит к верхнему регистру.
        Пример: "CEO of Company" -> "CEO_OF_COMPANY"
        """
        if not text:
            return "RELATED_TO"
        # Оставляем только буквы, цифры и подчеркивания
        clean = re.sub(r'[^a-zA-Z0-9_]', '_', text)
        # Убираем дублирующиеся подчеркивания и переводим в капс
        clean = re.sub(r'_+', '_', clean).strip('_').upper()
        return clean if clean else "RELATED_TO"


    def generate_cypher_queries(
        self,
        article: Article, 
        graph_data: AIKnowledgeGraph
    ) -> List[Tuple[str, Dict[str, Any]]]: # type: ignore
        """
        Возвращает список кортежей (Cypher Query, Parameters).
        """
        queries = []
        
        # Генерируем ID статьи
        article_id = self._generate_article_id(article)
        
        # ---------------------------------------------------------
        # 1. Запрос на создание Темы и Статьи
        # ---------------------------------------------------------
        # Логика:
        # - Тема (Topic) мержится (ищем или создаем).
        # - Статья (Article) создается (предполагаем, что она новая, или используем MERGE если возможны дубли).
        # - Связываем Article -> Topic.
        
        query_topic_article = """
        MERGE (t:Topic {name: $topic_name})
        ON CREATE SET 
            t.category = $category, 
            t.created_at = datetime()
        
        MERGE (a:Article {id: $article_id})
        ON CREATE SET 
            a.title = $article_title,
            a.date = $article_date,
            a.text_preview = $article_text_preview,
            a.created_at = datetime()

        MERGE (a)-[:COVERS]->(t)
        """
        
        params_topic_article = {
            "topic_name": graph_data.topic,
            "category": graph_data.category.value,
            "article_id": article_id,
            "article_title": article.name,
            "article_date": article.date,
            # Берем первые 200 символов для превью, чтобы не забивать базу
            "article_text_preview": article.text[:200] + "..." 
        }
        queries.append((query_topic_article, params_topic_article))

        # ---------------------------------------------------------
        # 2. Обработка Сущностей (Entities)
        # ---------------------------------------------------------
        # Логика:
        # - MERGE сущности по имени.
        # - Добавляем динамический лейбл (например, :Person).
        # - Обновляем описание ТОЛЬКО если старое было NULL/пустым, а новое есть.
        # - Связываем Article -> Mentions -> Entity.
        
        for entity in graph_data.entities:
            # Очищаем лейбл для Cypher (чтобы не было SQL/Cypher Injection)
            safe_label = self._sanitize_for_cypher(entity.label)
            # Добавляем базовый лейбл Entity для всех
            labels_str = f":Entity:{safe_label}"
            
            query_entity = f"""
            MERGE (e{labels_str} {{name: $name}})
            
            ON CREATE SET 
                e.description = $description,
                e.original_label = $label_raw
                
            ON MATCH SET
                e.description = CASE 
                    WHEN (e.description IS NULL OR e.description = "") AND ($description IS NOT NULL AND $description <> "")
                    THEN $description 
                    ELSE e.description 
                END
                
            WITH e
            MATCH (a:Article {{id: $article_id}})
            MERGE (a)-[:MENTIONS]->(e)
            """
            
            params_entity = {
                "name": entity.name,
                "description": entity.description,
                "label_raw": entity.label,
                "article_id": article_id
            }
            queries.append((query_entity, params_entity))

        # ---------------------------------------------------------
        # 3. Обработка Связей (Relationships)
        # ---------------------------------------------------------
        # Логика:
        # - Находим Source и Target узлы.
        # - Создаем связь с динамическим типом.
        # - В свойства связи пишем article_id, topic_id (для контекста).
        
        for rel in graph_data.relationships:
            safe_rel_type = self._sanitize_for_cypher(rel.type)
            
            query_rel = f"""
            MATCH (source:Entity {{name: $source_name}})
            MATCH (target:Entity {{name: $target_name}})
            MATCH (a:Article {{id: $article_id}})
            MATCH (t:Topic {{name: $topic_name}})
            
            -- Используем CREATE, так как одно и то же событие может повторяться в разных статьях
            -- Если нужна уникальность факта, можно использовать MERGE с проверкой свойств
            CREATE (source)-[r:{safe_rel_type}]->(target)
            
            SET r.context = $context,
                r.date = $date,
                r.article_id = a.id,
                r.topic_name = t.name,
                r.created_at = datetime()
            """
            
            params_rel = {
                "source_name": rel.source,
                "target_name": rel.target,
                "article_id": article_id,
                "topic_name": graph_data.topic,
                "context": rel.context,
                "date": rel.date
            }
            queries.append((query_rel, params_rel))

        return queries
        
    def create_indexes(self):
        # Important: Run this once to make lookups fast
        query = "CREATE CONSTRAINT IF NOT EXISTS FOR (n:Entity) REQUIRE n.name IS UNIQUE"
        with self.driver.session() as session:
            session.run(query)