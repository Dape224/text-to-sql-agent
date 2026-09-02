from langgraph.graph import add_messages
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage

from llm import brain
from state import AgentState


def generate_sql_node(state: AgentState):
    llm= brain()

    user_query = state.user_query
    database_schema= state.database_schema
    
    prompt= f"""
You are an Expert SQL Data Analyst specializing in DuckDB SQL. Your sole task is to translate natural language user queries into executable SQL statements based strictly on the provided database schema.

Database Schema:
{database_schema}

Instructions:
1. You must only generate SELECT statements. Do not generate INSERT, UPDATE, DELETE, DROP, or any other data modification commands.
2. You must use the exact table and column names provided in the schema. Do not invent, guess, or modify any identifiers.
3. If the user query cannot be answered using the provided schema, your entire response must be exactly: "I cannot answer this with the available data."
4. When filtering or comparing text-based columns (like names, departments, or product names), you MUST use case-insensitive matching. Use LOWER(column_name) = LOWER('value') or column_name ILIKE 'value'

Output Formatting:
- Output only the raw, plain-text SQL query.
- Do not include any markdown formatting or code blocks (do not use ```sql or ```).
- Do not include any explanations, greetings, introduction, or notes. 

User Query:
{user_query}
"""

    output = llm.invoke(
        [SystemMessage(content=prompt),
        HumanMessage(content= user_query)]
    )

    return {
        "agent_sql": output.content,
        "messages": [AIMessage(content=output.content)]
    }



        
    
