from typing import Annotated, Optional
from langgraph.graph import add_messages
from pydantic import BaseModel

class AgentState(BaseModel):
    user_query: str
    agent_sql: Optional[str] = None
    approval: Optional[bool] = False
    final_data: Optional[list[dict]] =None
    database_schema: str
    error_message: Optional[str] = None
    messages: Annotated[list, add_messages]
    summary_text: Optional[str]=None
    chart_path: Optional[str] = None
    chart_type: Optional[str] = None