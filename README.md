# 🤖 Enterprise-Grade Conversational SQL Agent (with Human-in-the-Loop)

> **"Stop waiting on the data team. Ask your database directly, safely, and conversationally."**

This project is a fully stateful, self-correcting AI Data Analyst that lives inside Slack. It translates natural language into SQL, executes it against a cloud Postgres database, and summarizes the results.

Unlike basic LLM wrappers, this agent is built for the enterprise. It features **Human-in-the-Loop (HITL) approval flows** to prevent destructive queries, **persistent memory** for multi-turn conversations, and **full observability** to track costs and latency.

---

## 🚀 Why This is Production-Ready

Most AI tutorials stop at "text-to-SQL." This project tackles the real-world engineering challenges required to deploy an AI agent safely in a corporate environment:

*   🛡️ **Human-in-the-Loop (HITL):** Using LangGraph `interrupts`, the agent pauses execution and sends interactive Slack buttons (✅ Approve / ❌ Reject) before running any query.
*   🧠 **Self-Correction Loops:** If the agent writes invalid SQL, the database error is caught and fed back to the LLM to rewrite the query autonomously.
*   💾 **Persistent State & Memory:** Powered by `PostgresSaver`, the agent's conversation history and paused threads survive server restarts. It understands context like *"What about Sarah's salary?"* without needing the user to repeat names.
*   📊 **Full Observability:** Every LLM call, token, and tool execution is traced in **Langfuse**, allowing engineers to debug failures and monitor API costs in production.
*   🔒 **Secure Integration:** Uses Slack's Socket Mode to listen for events via secure outbound WebSockets—no public IP addresses, ngrok, or exposed webhooks required.

---

## 🏗️ Architecture & Flow

The system is orchestrated using **LangGraph**, utilizing a Directed Acyclic Graph (DAG) with conditional routing:

1.  **`generate_sql_node`**: Takes the user's natural language query and the database schema to write a read-only `SELECT` statement.
2.  **`INTERRUPT`**: Execution pauses. The SQL is pushed to Slack with interactive approval buttons.
3.  **Human Approval**: 
    *   If ❌ **Rejected**, the graph halts.
    *   If ✅ **Approved**, the graph resumes.
4.  **`execute_sql_node`**: Runs the query via SQLAlchemy. If an error occurs, it routes back to Step 1 with the error message (Self-Correction).
5.  **`summarize_node`**: Takes the raw JSON data from Postgres and prompts the LLM to write a friendly, human-readable summary.
6.  **Output**: The final answer is posted back to the Slack channel.

---

## 🛠️ Tech Stack

*   **Orchestration:** LangGraph, LangChain
*   **Database & Checkpointer:** Supabase (Postgres) + `psycopg_pool`
*   **Database Toolkit:** SQLAlchemy (Database-agnostic schema inspection & execution)
*   **User Interface:** Slack Bolt (Socket Mode)
*   **LLM Provider:** OpenAI (`gpt-4o`)
*   **Observability:** Langfuse
*   **Deployment:** Render / Docker

---

## ⚙️ Local Setup & Installation

### 1. Prerequisites
*   Python 3.10+
*   A free [Supabase](https://supabase.com) project (for Postgres)
*   A free [Langfuse](https://cloud.langfuse.com) account (for tracing)
*   A [Slack App](https://api.slack.com/apps) with Socket Mode enabled.

### 2. Install Dependencies
```bash
python -m venv venv
source venv/bin/activate  # On Windows use `venv\Scripts\activate`
pip install -r requirements.txt