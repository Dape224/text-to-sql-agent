import os
import uuid
from typing import Literal, List, Dict
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

def render_chart(data: List[Dict], chart_type: Literal["bar", "line", "pie"]) -> str:
    """
    Renders a chart from SQL data and returns the local file path.
    """
    if not data:
        return "No data to plot."

    keys = list(data[0].keys())
    x_key = keys[0]
    y_key = keys[1] if len(keys) > 1 else keys[0] 
    
    labels = [str(row[x_key]) for row in data]
    values = [float(row[y_key]) for row in data] 

    os.makedirs("charts", exist_ok=True)
    filename = f"chart_{uuid.uuid4().hex}.png"
    filepath = os.path.join("charts", filename)

    fig, ax = plt.subplots(figsize=(8, 5))

    if chart_type == "bar":
        ax.bar(labels, values, color='teal', edgecolor='black')
        ax.set_xlabel(x_key.title())
        ax.set_ylabel(y_key.title())
        
    elif chart_type == "line":
        ax.plot(labels, values, marker='o', color='blue', linewidth=2)
        ax.set_xlabel(x_key.title())
        ax.set_ylabel(y_key.title())
        
    elif chart_type == "pie":
        ax.pie(values, labels=labels, autopct='%1.1f%%', startangle=140)
        
    else:
        plt.close(fig)
        return "Invalid chart type."

    ax.set_title(f"{chart_type.title()} Chart: {y_key} by {x_key}")
   
    fig.tight_layout()
    fig.savefig(filepath, dpi=150)
    plt.close(fig) 
    print(f"Successfully plotted: {filepath}")
    return filepath

if __name__ == "__main__":
    dummy_data = [
        {"department": "Engineering", "total_salary": 95000},
        {"department": "Sales", "total_salary": 75000},
        {"department": "Marketing", "total_salary": 65000}
    ]
    
    path = render_chart(dummy_data, "bar")
    print("Go open the 'charts' folder and look at the image!")