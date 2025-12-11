from contextlib import asynccontextmanager, contextmanager
import random
import time
import os
from neo4j import GraphDatabase, basic_auth
import spacy
from tqdm.contrib.concurrent import thread_map
from generator import Generator, measure_time
from google_gen import GoogleGenAI
from neo4j_manager import Neo4jGraphManager
from logger_config import get_logger
from dotenv import load_dotenv

logger = get_logger(__name__)
load_dotenv(override=True)
URI = "bolt://localhost:7687"
USER = "neo4j"
PASSWORD = "11111111"
auth=basic_auth(USER, PASSWORD)






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




def main():
    with neo() as driver:
        with driver.session() as session:
            result = session.run("MATCH (n) RETURN n LIMIT 5")
            for record in result:
                print(record.data())






if __name__ == "__main__":
    main()