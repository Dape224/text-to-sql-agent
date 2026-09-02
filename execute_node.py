from state import AgentState
from sqlalchemy import create_engine, text

from conn import get_engine


def execute_sql_node(state: AgentState):
    sql = state.agent_sql or  ""

    engine = get_engine()
    
    with engine.connect() as conn:
        try:
            output = conn.execute(text(sql))
            data = [dict(row) for row in output.mappings()]

            return {
            "final_data": data,
            "error_message": None
            }

        except Exception as e:
            error_message = str(e)
            return {
            "final_data": None,
            "error_message": error_message
        }