import os
import uuid
import streamlit as st
from langchain_core.messages import HumanMessage
from agent import analyst
from conn import setup_db_and_get_schema

st.set_page_config(page_title="Nexus Logistics Data Analyst", page_icon="📊", layout="wide")
st.title("📊 Nexus Logistics AI Data Analyst")
st.caption("Ask in plain English. The agent writes SQL, waits for your approval, then answers with insights + charts.")

# session_state survives the rerun
for key, val in [("thread_id", None), ("pending_sql", None), ("answer", None), ("chart_path", None)]:
    if key not in st.session_state:
        st.session_state[key] = val

question = st.text_input("Ask a question about the data:")

if st.button("Ask", type="primary") and question:
    thread_id = str(uuid.uuid4())
    st.session_state.thread_id = thread_id
    st.session_state.answer = None
    st.session_state.chart_path = None
    schema = setup_db_and_get_schema()
    config = {"configurable": {"thread_id": thread_id}}
    initial_state = {"user_query": question, "database_schema": schema,
                     "messages": [HumanMessage(content=question)]}
    output = analyst.invoke(initial_state, config=config)
    st.session_state.pending_sql = output["agent_sql"]

# --- Human-in-the-Loop approval UI ---
if st.session_state.pending_sql:
    st.subheader("🔍 Generated SQL — Approval Required")
    st.code(st.session_state.pending_sql, language="sql")
    colA, colB = st.columns(2)
    with colA:
        if st.button("✅ Approve & Run"):
            # YOUR TASK: resume the graph (same as Slack handle_approve)
            # 1. build config from st.session_state.thread_id
            # 2. analyst.update_state(config, {"approval": True})
            # 3. final = analyst.invoke(None, config=config)
            # 4. store final["summary_text"] and final["chart_path"] into session_state
            # 5. clear pending_sql, then st.rerun()
            pass
    with colB:
        if st.button("❌ Reject"):
            st.session_state.pending_sql = None
            st.rerun()

# --- Results ---
if st.session_state.answer:
    st.subheader("💡 Insight")
    st.write(st.session_state.answer)
if st.session_state.chart_path and os.path.exists(st.session_state.chart_path):
    st.subheader("📈 Chart")
    st.image(st.session_state.chart_path, use_container_width=True)