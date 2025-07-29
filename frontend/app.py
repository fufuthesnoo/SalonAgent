import gradio as gr
import requests
import json
from sseclient import SSEClient

BACKEND_URL = "http://backend:8000"


def ask_agent(question: str):
    """Send the question to the backend and stream the agent’s reply."""
    # 1️⃣  Kick off a new session
    resp = requests.post(f"{BACKEND_URL}/ask", params={"question": question})
    resp.raise_for_status()
    ticket = resp.json()["ticket"]

    # 2️⃣  Open the Server‑Sent Events stream
    stream_resp = requests.get(f"{BACKEND_URL}/stream/{ticket}", stream=True)
    client = SSEClient(stream_resp)          # hand the Response object to SSEClient

    # 3️⃣  Relay incremental updates to Gradio
    messages: list[str] = []
    for event in client.events():
        data = json.loads(event.data)
        if data["type"] == "log":
            yield "\n".join(messages + [f"🔸 {data['message']}"])
        elif data["type"] == "answer":
            messages.append(f"🟢 {data['answer']}")
            yield "\n".join(messages)
        elif data["type"] == "done":
            break


with gr.Blocks(title="SalonData Agent") as demo:
    gr.Markdown("### Ask a business question:")
    chat_log = gr.Textbox(
        label="Session log",
        lines=12,
        interactive=False,
        autofocus=False,
    )
    user_input = gr.Textbox(label="Your question", autofocus=True)
    user_input.submit(ask_agent, inputs=user_input, outputs=chat_log)

if __name__ == "__main__":
    demo.launch(server_name="0.0.0.0", server_port=7860)
