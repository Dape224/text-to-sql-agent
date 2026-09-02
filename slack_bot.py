import os
import re
import uuid
import threading
from fastapi import FastAPI
import uvicorn
from dotenv import load_dotenv
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler
from langchain_core.messages import HumanMessage
from langfuse.langchain import CallbackHandler

from agent import analyst
from conn import setup_db_and_get_schema

load_dotenv()

app = App(token=os.environ.get("SLACK_BOT_TOKEN"))

langfuse_handler = CallbackHandler()

web = FastAPI()

@web.get("/")
def heartbeat():
    return {"status": "alive"}   

def run_web():
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(web, host="0.0.0.0", port=port)

@app.event("app_mention")
def handle_mention(event, say):
    raw_text = event.get("text", "")
    question = re.sub(r"<@[^>]+>", "", raw_text).strip()

    if not question:
        say("Please ask me a question about the data! 🙂")
        return

    thread_id = str(uuid.uuid4())

    schema = setup_db_and_get_schema()
    initial_state = {
        "user_query": question,
        "database_schema": schema,
        "messages": [HumanMessage(content=question)],
    }
    config = {
        "configurable": {"thread_id": thread_id},
        "callbacks": [langfuse_handler],
        "run_name": "slack_sql_agent",
    }

    output = analyst.invoke(initial_state, config=config)
    sql = output["agent_sql"]

    say(
        text=f"Generated SQL for: {question}",
        blocks=[
            {
                "type": "section",
                "text": {"type": "mrkdwn",
                         "text": f"*Generated SQL:*\n```{sql}```\nDo you approve?"},
            },
            {
                "type": "actions",
                "elements": [
                    {
                        "type": "button",
                        "text": {"type": "plain_text", "text": "✅ Approve"},
                        "style": "primary",
                        "action_id": "approve_sql",
                        "value": thread_id,  
                    },
                    {
                        "type": "button",
                        "text": {"type": "plain_text", "text": "❌ Reject"},
                        "style": "danger",
                        "action_id": "reject_sql",
                        "value": thread_id,
                    },
                ],
            },
        ],
    )


@app.action("approve_sql")
def handle_approve(ack, body, client):
    ack()

    thread_id = body["actions"][0]["value"]
    channel_id = body["channel"]["id"]
    config = {"configurable": {"thread_id": thread_id}}

    analyst.update_state(config, {"approval": True})
    final_output = analyst.invoke(None, config=config)

    answer = final_output.get("summary_text") or "Here is the data."
    chart_path = final_output.get("chart_path")

    if chart_path and os.path.exists(chart_path):
        client.files_upload_v2(
            channel=channel_id,
            file=chart_path,
            title="Generated Chart",
            initial_comment=f"📊 {answer}"
        )
        os.remove(chart_path)
    else:
        client.chat_postMessage(channel=channel_id, text=f"📊 {answer}")

@app.action("reject_sql")
def handle_reject(ack, body, client):
    ack()
    channel_id = body["channel"]["id"]
    client.chat_postMessage(
        channel=channel_id,
        text="❌ SQL rejected. Ask me a different question!",
    )


if __name__ == "__main__":
    threading.Thread(target=run_web, daemon=True).start()

    handler = SocketModeHandler(app, os.environ.get("SLACK_APP_TOKEN"))
    print("⚡ Slack bot is running...")
    handler.start()

