import os
import uuid
import streamlit as st
from langchain_core.messages import HumanMessage
from agent import analyst
from conn import setup_db_and_get_schema

st.set_page_config(page_title="Nexus Logistics Data Analyst", page_icon="📊", layout="wide")
st.title("📊 Nexus Logistics AI Data Analyst")
st.caption("Ask in plain English. The agent writes SQL, waits for your approval, then answers with insights + charts.")

SAMPLE_QUESTIONS = {
    "📊 Bar Charts": [
        "Show me a bar chart of daily processed packages by hub name",
        "Show me a bar chart of total shipping revenue by carrier service",
        "Show me a bar chart of total active robots by hub name",
        "Show me a bar chart of average CSAT score by platform type",
        "Show me a bar chart of warehouse capacity percentage by hub name",
    ],
    "🥧 Pie Charts": [
        "Show me a pie chart of shipment orders by delivery status",
        "Show me a pie chart of orders by carrier service",
        "Show me a pie chart of fulfillment centers by global region",
        "Show me a pie chart of support tickets by category",
        "Show me a pie chart of total active users by platform type",
    ],
    "📈 Line Charts": [
        "Show me a line chart of total active users over time",
        "Show me a line chart of daily shipping revenue over time",
        "Show me a line chart of average CSAT score over time",
        "Show me a line chart of total orders per day over time",
    ],
    "💬 Plain Data": [
        "How many shipment orders do we have in total?",
        "What is our total shipping revenue?",
        "Which fulfillment hub processes the most packages per day?",
        "How many orders are currently delayed?",
        "What is the average customer satisfaction score?",
        "Which carrier service generates the most revenue?",
        "How many robots are active in the TOK-02 hub?",
        "Which region has the most fulfillment centers?",
    ],
}

for key, val in [("thread_id", None), ("pending_sql", None), ("answer", None), ("chart_path", None)]:
    if key not in st.session_state:
        st.session_state[key] = val

with st.expander("🎯 Don't know what to ask? Pick a sample question"):
    cat = st.selectbox("Category", list(SAMPLE_QUESTIONS.keys()), key="sample_cat")
    picked = st.selectbox("Sample question", SAMPLE_QUESTIONS[cat], key="sample_q")
    if st.button("Load question ⬆️"):
        st.session_state["question_input"] = picked
        st.rerun()

question = st.text_input("Ask a question about the data:", key="question_input")

if st.button("Ask", type="primary") and question:
    thread_id = str(uuid.uuid4())
    st.session_state.thread_id = thread_id
    st.session_state.answer = None
    st.session_state.chart_path = None
    st.session_state.pending_sql = None

    schema = setup_db_and_get_schema()
    config = {"configurable": {"thread_id": thread_id}}
    initial_state = {
        "user_query": question,
        "database_schema": schema,
        "messages": [HumanMessage(content=question)],
    }

    with st.spinner("🤖 Agent is analyzing your question and writing SQL..."):
        output = analyst.invoke(initial_state, config=config)

    st.session_state.pending_sql = output["agent_sql"]
    st.rerun()

if st.session_state.pending_sql:
    st.subheader("🔍 Generated SQL — Approval Required")
    st.code(st.session_state.pending_sql, language="sql")

    colA, colB = st.columns(2)
    with colA:
        if st.button("✅ Approve & Run", type="primary"):
            config = {"configurable": {"thread_id": st.session_state.thread_id}}
            with st.spinner("⚙️ Running approved SQL and building your insight..."):
                analyst.update_state(config, {"approval": True})
                final = analyst.invoke(None, config=config)

            if final.get("summary_text"):
                st.session_state.answer = final.get("summary_text")
                st.session_state.chart_path = final.get("chart_path")
                st.session_state.pending_sql = None
            else:
                st.session_state.pending_sql = final.get("agent_sql")
                st.session_state.answer = None
            st.rerun()

    with colB:
        if st.button("❌ Reject"):
            st.session_state.pending_sql = None
            st.session_state.answer = None
            st.rerun()

if st.session_state.answer:
    st.divider()
    st.subheader("💡 Insight")
    st.write(st.session_state.answer)

if st.session_state.chart_path and os.path.exists(st.session_state.chart_path):
    st.subheader("📈 Chart")
    st.image(st.session_state.chart_path, use_container_width=True)