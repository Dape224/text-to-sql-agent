import os
import uuid
import streamlit as st
from langchain_core.messages import HumanMessage
from agent import analyst
from conn import setup_db_and_get_schema

st.set_page_config(page_title="Nexus Logistics Data Analyst", page_icon="📊", layout="wide")
st.title("📊 Nexus Logistics AI Data Analyst")
st.caption("Ask in plain English. The agent writes SQL, waits for your approval, then answers with insights + charts.")

for key, val in [("thread_id", None), ("pending_sql", None), ("answer", None), ("chart_path", None)]:
    if key not in st.session_state:
        st.session_state[key] = val

question = st.text_input("Ask a question about the data:")

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