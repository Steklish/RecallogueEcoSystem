import os
import re
import time
from typing import Optional, List

import httpx

from app.src.services.ai_backends.generator import ai_generator as generator
from app.src.services.chroma_client import ChromaClient
from app.src.utils.colors import *

# Import necessary schemas
from app.src.services.ai_backends.schemas import *

MAX_ITERATIONS = os.getenv("AI_AGENT_MAX_ITERATIONS", 3)

class Agent:
    def __init__(self, language : str = "Russian"):
        self.language = language

    def user_intent(self, thread_id : int, temperature:float = 0.5) -> str:
        ...

     
def _exec_queries(query_list : DataBaseQueryList):
    results = []
    for query in query_list.sql_queries:
            print(f"{INFO_COLOR}Generated SQL query: {query} {RESET}")
            try:
                if 'UNION' in query:
                    for clean_query in _split_union_query(query):
                        query_results = httpx.get(f"http://127.0.0.1:{int(os.getenv('MCP_PORT', 1234))}/api/database/query", params={"query": clean_query})
                        results.append(
                            {
                                "query": clean_query,
                                "results": query_results.json().get("results", []),
                            }
                        )    
                else:
                    query_results = httpx.get(f"http://127.0.0.1:{int(os.getenv('MCP_PORT', 1234))}/api/database/query", params={"query": query})
                    results.append(
                        {
                            "query": query,
                            "results": query_results.json().get("results", []),
                        }
                    )
            except Exception as e:
                results.append(
                    {
                        "query": query,
                        "results": f"Error executing query: {e}",
                    }
                )  
    
def _split_union_query(sql_query: str) -> List[str]:
    """
    Splits a single SQL query string containing UNION or UNION ALL 
    into a list of individual SELECT queries.

    This function is case-insensitive and handles variable whitespace.

    Args:
        sql_query: The full SQL query string.

    Returns:
        A list of the individual SELECT query strings, with whitespace trimmed.
    """
    if not sql_query:
        return []

    # Regex to split on "UNION" or "UNION ALL", surrounded by whitespace.
    # re.IGNORECASE makes the split case-insensitive (e.g., matches 'union', 'Union').
    # The pattern looks for 'UNION' optionally followed by ' ALL', surrounded by spaces.
    pattern = r'\s+UNION(?:\s+ALL)?\s+'
    
    # Split the query based on the pattern
    queries = re.split(pattern, sql_query.strip(), flags=re.IGNORECASE)
    
    # Clean up any potential empty strings and strip each query
    # This handles queries that might start/end with UNION or have multiple UNIONs in a row
    cleaned_queries = [q.strip() for q in queries if q.strip()]
    
    return cleaned_queries
    
    
    
class PlanningAgent:
    
    def plan (self, query: str, sources_list) -> TaskList:
        
        prompt = f"""
# 🧑‍💻 ROLE:
You are an expert AI Planning Agent. Your primary function is to analyze a user's request and formulate a logical, step-by-step plan to fulfill it using a predefined set of tools.

# 🎯 PRIMARY GOAL:
To create a clear, efficient, and actionable plan as a sequence of discrete tasks that directly addresses the user's query. The final output MUST be a list of tasks.

# 📝 CORE INSTRUCTIONS & PRINCIPLES:
1.  **Deconstruct the Request**: Break down the user's query into smaller, manageable sub-goals.
2.  **Logical Sequencing**: Arrange the tasks in a logical order where each step builds upon the previous one.
3.  **Tool-Oriented Planning**: Each task in your plan should correspond to a logical operation that can be accomplished with the available tools. Map tasks to tools where appropriate.
4.  **Clarity and Simplicity**: The plan should be easy to understand. Use clear and concise language for each step.
5.  **Efficiency**: Create the most direct plan to achieve the user's goal without unnecessary steps.
6.  **Handle Ambiguity**: If the user's request is vague or ambiguous, the first step in your plan should be to ask clarifying questions.

# 🛠️ AVAILABLE TOOLS:
The tools available to you are defined in the following list: `{sources_list}`.
- You MUST only plan to use the tools provided in this list.
- For each tool, consider its purpose and what information it requires to function.

# 📜 OUTPUT FORMAT and CONSTRAINTS:
- Your output MUST be a plan consisting of a step-by-step list.
- Do not generate any introductory text, summary, or explanation outside of the plan itself.
- Do not attempt to execute the plan or generate the results of the steps. Your only job is to create the plan.

#  EXEMPLARY EXAMPLES (Few-Shot Learning):

---
**EXAMPLE 1**

**User Query**: "My request is to find info about out Mr. Johnes and compare his incomes to average."
**Available Tools**: `[search_biography(person_name: str), find_salary(person_name: str, location: str), calculate_average_salary(industry: str, location: str)]`

**Generated Plan**:
- Find biographical information for "Mr. Johnes" to identify his industry and location using the `search_biography` tool.
- Find the specific income of "Mr. Johnes" using the `find_salary` tool with his name and location.
- Calculate the average salary for his identified industry and location using the `calculate_average_salary` tool.
- Compare Mr. Johnes's income with the calculated average income to determine the difference.

---
**EXAMPLE 2**

**User Query**: "What were the top 3 selling products for our company last quarter, and how did their sales trend over the past year?"
**Available Tools**: `[query_sales_database(query: str), analyze_trends(data: list)]`

**Generated Plan**:
- Query the sales database to get the top 3 selling products from the last quarter.
- For each of the top 3 products, query the sales database for their monthly sales figures over the past 12 months.
- Analyze the collected sales data to identify trends for each of the top products.
- Synthesize the findings to present the top 3 products and their corresponding sales trends.

---

# 📥 USER REQUEST:
Here is the user's request you need to process:

**User Query**: "{query}"
"""
        
        task_list : TaskList = generator.generate_one_shot(
            pydantic_model=TaskList,
            prompt=prompt
        )
        
        return task_list
    
    def task_to_subtasks(self, task : Task):
        ...