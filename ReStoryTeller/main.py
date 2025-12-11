from contextlib import asynccontextmanager, contextmanager
import os
from neo4j import GraphDatabase, basic_auth
from tqdm.contrib.concurrent import thread_map
from generator import Generator, measure_time
from google_gen import GoogleGenAI
from logger_config import get_logger
from dotenv import load_dotenv
from processor import Processor
from neo4j_manager import Neo4jGraphManager
from sqlite_entity_manager import SQLiteEntityManager
from chroma_client import ChromaClient
from embedding_client import EmbeddingClient


from schemas import AIKnowledgeGraph

logger = get_logger(__name__)

load_dotenv(override=True)
URI = os.getenv("NEO_URI")
USER = os.getenv("NEO_USER")
PASSWORD = os.getenv("NEO_PASSWORD")

if not URI or not USER or not PASSWORD:
    logger.error("Neo4j connection details are not fully set in environment variables.")
    raise ValueError("Missing Neo4j connection details.")

auth=basic_auth(USER, PASSWORD)

processor = Processor(SQLiteEntityManager("entities.db"), ChromaClient(EmbeddingClient()), Generator(GoogleGenAI()))


   
@measure_time
def load_from_list(filename):
    if not os.path.exists(filename):
        logger.error(f"List file not found: {filename}")
        return

    with open(filename, "r", encoding="utf-8") as f:
        filename_list = f.readlines()
        
    # Process files
    # results = thread_map(process_file, filename_list, max_workers=5)        



if __name__ == "__main__":
    ...