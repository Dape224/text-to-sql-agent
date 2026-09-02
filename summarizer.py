from state import AgentState
from llm import brain

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage

def summary_node(state: AgentState) -> str:
    user_query= state.user_query 
    final_data= state.final_data or ""

    llm = brain()

    prompt = f"""
You are a friendly Senior Business Intelligence Analyst for Nexus Logistics Global.
A SQL query was run against the company database and returned the raw data below.

User Question:
{user_query}

Raw Data:
{final_data}

Your ONLY job is to write a SHORT, conversational summary of the key insights.

STRICT RULES:
1. Keep it to 2-4 sentences. Highlight the most interesting points (top performer, lowest, trends, or outliers).
2. NEVER include Python code, matplotlib/Excel/Sheets instructions, or "how to plot it yourself" steps.
3. NEVER say "I can't generate images" or "I can't create charts." If the user asked for a visual, the system AUTOMATICALLY attaches the chart for you. Your text is only the insight summary.
4. Do NOT list every row of raw data. Summarize the story the data tells.
5. Write like you're talking to a colleague on Slack — warm, sharp, and concise.
"""

    output = llm.invoke([
        SystemMessage(content= prompt),
        HumanMessage(content= user_query)
    ])

    return {
        "summary_text": output.content,
        "messages": [AIMessage(content=output.content)]
    }
