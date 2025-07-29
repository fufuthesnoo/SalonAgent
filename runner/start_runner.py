from fastapi import FastAPI
from typing import List, Dict, Any
import uvicorn
import asyncio

from computer_playwright import ComputerPlaywright

app = FastAPI(title="Computer Runner")
cp = ComputerPlaywright()           # one singleton browser per container

@app.post("/execute")
async def execute(actions: List[Dict[str, Any]]):
    """
    Body: JSON array of computer‑tool actions.
    Returns whatever the final 'finish' action supplied, or {"status":"ok"}.
    """
    result = await cp.run(actions)
    return result

if __name__ == "__main__":
    uvicorn.run("start_runner:app", host="0.0.0.0", port=3000)
