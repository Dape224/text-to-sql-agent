from langgraph.graph import END
from state import AgentState
from visualize import render_chart 

def route_after_summary(state: AgentState) -> str:
    """
    Checks if the user asked for a visual AND if the data is suitable for a chart.
    """
    user_query = (state.user_query or "").lower()
    final_data = state.final_data

    visual_keywords = ["chart", "graph", "plot", "visual", "visualize"]
    wants_chart = any(keyword in user_query for keyword in visual_keywords)

    is_chartable = (
        final_data is not None 
        and len(final_data) > 0 
        and len(final_data[0].keys()) >= 2
    )

    if wants_chart and is_chartable:
        return "visualize"
   
    return END


def visualize_node(state: AgentState) -> dict:
    """
    Determines the best chart type based on the prompt, generates it, and updates state.
    """
    user_query = (state.user_query or "").lower()
    final_data = state.final_data

    if "pie" in user_query:
        chart_type = "pie"
    elif "line" in user_query or "trend" in user_query or "time" in user_query or "over time" in user_query:
        chart_type = "line"
    else:
        chart_type = "bar" 

    try:
        path = render_chart(final_data, chart_type)
        
        return {
            "chart_path": path,
            "chart_type": chart_type
        }
    except Exception as e:
        print(f"Error generating chart: {e}")
        return {
            "chart_path": None,
            "chart_type": chart_type
        }