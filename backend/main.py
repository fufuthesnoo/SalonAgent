import os, asyncio, json, queue, requests
from fastapi import FastAPI, BackgroundTasks
from fastapi.responses import StreamingResponse, JSONResponse
from uuid import uuid4

app = FastAPI(title="SalonData Agent API")
sessions: dict[str, "queue.Queue[dict]"] = {}

RUNNER_URL = os.getenv("RUNNER_URL", "http://runner:3000")

@app.post("/ask")
async def ask(question: str, background_tasks: BackgroundTasks):
    ticket = str(uuid4())
    q = queue.Queue()
    sessions[ticket] = q
    background_tasks.add_task(run_agent_session, ticket, question)
    return {"ticket": ticket}

@app.get("/stream/{ticket}")
async def stream(ticket: str):
    if ticket not in sessions:
        return JSONResponse({"error": "unknown ticket"}, status_code=404)

    q = sessions[ticket]

    async def event_source():
        while True:
            item = await asyncio.get_event_loop().run_in_executor(None, q.get)
            yield f"data: {json.dumps(item)}\n\n"
            if item.get("type") == "done":
                break

    return StreamingResponse(event_source(), media_type="text/event-stream")

async def run_agent_session(ticket: str, question: str):
    q = sessions[ticket]
    q.put_nowait({"type": "log", "message": f"Received: {question}"})

    # 🔹  Demo action list — proof Playwright can drive a real browser
    actions = [
        {"name": "navigate", "url": "https://example.com"},
        {"name": "click",    "selector": "text=More information"},
        {
            "name": "finish",
            "reason": "demo complete",
            "answer": "Opened example.com and clicked the More‑info link.",
        },
    ]

    q.put_nowait({"type": "log", "message": "Sending actions to runner…"})

    try:
        resp = requests.post(f"{RUNNER_URL}/execute", json=actions, timeout=300)
        resp.raise_for_status()
        runner_out = resp.json()
        q.put_nowait({"type": "log", "message": f"Runner result: {runner_out}"} )
        answer_txt = runner_out.get("answer", "Runner finished.")
    except Exception as exc:
        answer_txt = f"Runner failed: {exc}"
        q.put_nowait({"type": "log", "message": answer_txt})

    q.put_nowait({"type": "answer", "answer": answer_txt})
    q.put_nowait({"type": "done"})