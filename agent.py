import os
import uuid
from dotenv import load_dotenv

from langgraph.graph import START, END, StateGraph
from langchain_core.messages import HumanMessage
from psycopg_pool import ConnectionPool
from langgraph.checkpoint.postgres import PostgresSaver
from langfuse import get_client
from langfuse.langchain import CallbackHandler

from generate_node import generate_sql_node
from execute_node import execute_sql_node
from summarizer import summary_node
from plot_node import visualize_node, route_after_summary
from state import AgentState
from conn import setup_db_and_get_schema

load_dotenv()

DB_URI = os.getenv("DATABASE_URL")

def route_after_execution(state: AgentState):
    if state.error_message:
        return "generate_sql_node"

    if state.approval == False:
        return END
    return "summary_node"


graph = StateGraph(AgentState)

graph.add_node("generate_sql_node", generate_sql_node)
graph.add_node("execute_sql_query", execute_sql_node)
graph.add_node("summary_node", summary_node)
graph.add_node("visualize", visualize_node)

graph.add_edge(START, "generate_sql_node")
graph.add_edge("generate_sql_node", "execute_sql_query")
graph.add_conditional_edges(
    "execute_sql_query",
    route_after_execution,
    {"generate_sql_node": "generate_sql_node",
     "summary_node": "summary_node"}
)


graph.add_conditional_edges(
    "summary_node",
    route_after_summary,
    {"visualize": "visualize", END: END}
)

graph.add_edge("visualize", END)

pool = ConnectionPool(
    conninfo=DB_URI,
    kwargs={"autocommit": True, "prepare_threshold": None},
)
checkpointer = PostgresSaver(pool)
try:
    checkpointer.setup()
except Exception as e:
    if "already exists" in str(e).lower():
        pass
    else:
        raise e

analyst = graph.compile(checkpointer=checkpointer, interrupt_before=["execute_sql_query"])

def test_analyst():
    langfuse_handler = CallbackHandler()

    config = {
        "configurable": {"thread_id": uuid.uuid4()},
        "callbacks": [langfuse_handler],
        "run_name": "text-to-sql-agent"
    }

    while True:
        user_query = input("You: ")

        if user_query in ["exit", "quit"]:
            break

        schema = setup_db_and_get_schema()

        initial_state = {
            "user_query": user_query,
            "database_schema": schema,
            "messages": [HumanMessage(content=user_query)]
        }

        output = analyst.invoke(initial_state, config=config)

        generated_sql = output["agent_sql"]

        print(f"\n--- Generated SQL ---")
        print(generated_sql)
        print("---------------------\n")

        approval = input("Do you approve this SQL? (yes/no): ").strip().lower()
        if approval == "yes":
            analyst.update_state(config, {"approval": True})
            final_output = analyst.invoke(None, config=config)

            print(final_output["summary_text"])

            if final_output.get("chart_path"):
                print(f"\n📊 Chart saved at: {final_output['chart_path']}")
        else:
            analyst.update_state(config, {"approval": False, "error_message": "SQL rejected by human"})
            print("SQL rejected. Please ask a different question.\n")

        get_client().flush()

    get_client().flush()

if __name__ == "__main__":
    test_analyst()