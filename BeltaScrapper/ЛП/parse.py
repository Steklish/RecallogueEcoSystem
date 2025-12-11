from pprint import pprint
import random
import time
import os
import logging
import spacy
from tqdm.contrib.concurrent import thread_map

from generator import Generator, measure_time
from lcpp_gen import LlamaCppGenAI
from google_gen import GoogleGenAI
from neo4j_manager import Neo4jGraphManager
from entity_normalizer import EntityNameNormalizer
from schemas import KnowledgeGraph
from logger_config import get_logger
from utils import apply_to_all_files

logger = get_logger(__name__)

# Load Spacy
try:
    nlp = spacy.load("ru_core_news_lg")
except OSError:
    logger.warning("Spacy model 'ru_core_news_lg' not found. Please install it using: python -m spacy download ru_core_news_lg")
    # Fallback to prevent crash if not installed, though detection will fail
    nlp = None 

# Initialize Components
generator = Generator(client=GoogleGenAI())
normalizer = EntityNameNormalizer()
neo = Neo4jGraphManager(uri="bolt://localhost:7687", auth=("neo4j", "11111111"))

# Ensure indexes exist to prevent duplication race conditions
try:
    neo.create_indexes()
except Exception as e:
    logger.warning(f"Could not create indexes: {e}")


# Configure Nebula (using defaults/placeholders as requested)
# nebula = NebulaGraphManager(
#     address="127.0.0.1", port=9669, 
#     user="root", password="nebula", space="knowledge_graph"
# )

def detect_names(text: str) -> list[str]:
    """Detect potential entity names in the text using Spacy."""
    if not nlp:
        return []
    
    # Increase max length for large files
    nlp.max_length = max(len(text) + 1000, nlp.max_length)
    
    doc = nlp(text)
    # Extract entities relevant for context lookup (Person, Org, GPE, Loc)
    names = set([ent.text for ent in doc.ents if ent.label_ in ["PER", "ORG", "LOC", "GPE"]])
    return list(set(names))

def get_KG_from_text(text, context_info=""):
    # LLM generates pydantic schema
    prompt_content = f"""
        Используй следующие имена, в том виде, в каком они встречаются поле `известные имена`, если они есть. Если их нет или они не относятся к контексту статьи, просто игнорируй это поле.
        <известные имена>
        {context_info}
        </известные имена>
        <начало статьи>
        {text}
        <конец статьи>

        """

    instructions = """
        Сгенерируй граф знаний. Следуй этим строгим правилам моделирования:

        1. НЕ сохраняй "Должность" или "Местоположение" как свойство внутри Человека.
        2. Вместо этого создай отдельную Сущность (Label: 'Role' или 'Location').
        3. Создай связь между Человеком и Ролью.
        4. Связи (Relationships) должны содержать поле "reasoning", объясняющее причину создания этой связи.
        5. ХРАНИ ВСЕ ДАТЫ в СВЯЗЯХ, а не в сущностях. Используй поля start_date, end_date, date.
        6. НЕ используй свойства даты (birth_date, etc.) в Сущностях, если они чувствительны к времени.
        7. ИСПОЛЬЗУЙ описания сущностей из справочной информации при генерации текста и сохранении сущностей.
        8. НЕ создавай сущности, если нет информации для их идентификации (рабочий из г. Минск - невозможно опознать).
        
        ### ПРАВИЛА ИМЕНОВАНИЯ (STYLE GUIDE)

        **А. Сущности (Entities):**
        *   **name:** Используй каноническое, полное имя на языке оригинала в именительном падеже (начальной форме). Для имен, если возможно, используй полное имя и фамилию.
            *   Пример: "Владимир Путин", "Премьер-министр России".
        *   **label:** Используй **Английский язык**, PascalCase, Единственное число.
            *   Разрешенные Label: [Person, Organization, Country, City, Role, Event, Document, Resource].
        *   **description:** Если для сущности есть описание в справочной информации, обязательно включи его в сгенерированную сущность.

        **Б. Связи (Relationships):**
        *   **type:** Используй **Английский язык**, UPPER_SNAKE_CASE. Описывай действие.
            *   Пример: HELD_POSITION, SIGNED_CONTRACT, MADE_STATEMENT, LOCATED_IN.
        *   **reasoning:** Краткое описание, почему эта связь существует.
        *   **start_date:** Начальная дата отношения (формат: 'YYYY-MM-DD').
        *   **end_date:** Конечная дата отношения (формат: 'YYYY-MM-DD').
        *   **date:** Конкретная дата события (формат: 'YYYY-MM-DD').

        **В. Свойства (Properties):**
        *   **context:** Дополнительный контекст.
    """

    res = generator.generate_one_shot(
        pydantic_model=KnowledgeGraph,
        language="Russian",
        prompt=prompt_content + instructions
    )
    return res

def process_file(filename):
    clean_filename = filename.strip()
    if not os.path.exists(clean_filename):
        logger.error(f"File not found: {clean_filename}")
        return

    try:
        with open(clean_filename, "r", encoding="utf-8") as f:
            text = f.read()
        
        # Artificial delay from original code
        time.sleep(random.randint(0, 20) / 10)
        
        # 1. Pipeline: Detect Names & Get Context
        detected_names = detect_names(text)
        context_matches = normalizer.get_relevant_context(detected_names)

        context_str = ""
        if context_matches:
            context_str = "/n### СПРАВОЧНАЯ ИНФОРМАЦИЯ (КОНТЕКСТ):/n"
            for match in context_matches:
                if match.get('description'):
                    context_str += f"- {match['original_name']} -> {match['matched_name']} (Описание: {match['description']})/n"
                else:
                    context_str += f"- {match['original_name']} -> {match['matched_name']}/n"
            logger.info(f"Found {len(context_matches)} context items for {clean_filename}")

        res = get_KG_from_text(text, context_str)

        logger.info(f"Saving to Neo4j: {clean_filename}")
        neo.execute_graph(res, filename) # type: ignore
            
    except Exception as e:
        logger.error(f"Error processing file {clean_filename}: {e}", exc_info=True)
        return
   
@measure_time
def load_from_list(filename):
    if not os.path.exists(filename):
        logger.error(f"List file not found: {filename}")
        return

    with open(filename, "r", encoding="utf-8") as f:
        filename_list = f.readlines()
        
    # Process files
    results = thread_map(process_file, filename_list, max_workers=5)        

if __name__ == "__main__":
    # Clear DB if needed, or keeping persistent. 
    # neo.clear_entities_db() # Warning: This wipes the normalizer DB too! Use with caution.
    
    # Determine the directory where this script is located
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Run
    # Construct absolute path to info.md
    # info_md_path = os.path.join(script_dir, "info.md")
    # process_file(info_md_path)
    for day in range(18, 31):
        dir_path = f"D:/Duty/BeltaScrapper/data/2011/{day:02d}.03.2011"
        apply_to_all_files(dir_path, process_file)
    
    
    # load_from_list(os.path.join(script_dir, "both.txt"))
    # Cleanup
    neo.close()
    # nebula.close()