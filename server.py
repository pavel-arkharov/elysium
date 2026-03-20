#!/usr/bin/env python3
"""
server.py — FastAPI entrypoint for agent-bar web interface.

Usage:
    python3 server.py
    python3 server.py --scene config/scene.yaml --port 8000
"""

import argparse
import asyncio
from contextlib import asynccontextmanager
from pathlib import Path

import uvicorn
import yaml
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from core.agent import Agent
from core.transcript import Transcript


# ---------------------------------------------------------------------------
# Global state
# ---------------------------------------------------------------------------

_connected: set[WebSocket] = set()
_loop_task: asyncio.Task | None = None
_scene: dict = {}
_agents: list[Agent] = []


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _load_scene(scene_path: str) -> tuple[dict, list[Agent]]:
    path = Path(scene_path)
    with open(path) as f:
        scene = yaml.safe_load(f)

    agents = []
    for p in scene.get("cast", []):
        with open(path.parent / p) as f:
            agents.append(Agent(yaml.safe_load(f)))

    return scene, agents


async def _broadcast(data: dict) -> None:
    dead = set()
    for ws in _connected:
        try:
            await ws.send_json(data)
        except Exception:
            dead.add(ws)
    _connected.difference_update(dead)


# ---------------------------------------------------------------------------
# Conversation loop
# ---------------------------------------------------------------------------

async def _conversation_loop() -> None:
    transcript = Transcript(
        setting=_scene.get("setting", ""),
        opening=_scene.get("opening", ""),
    )

    await _broadcast({
        "type": "scene",
        "title": _scene.get("title", ""),
        "setting": _scene.get("setting", ""),
        "opening": _scene.get("opening", ""),
    })

    index = 0
    while True:
        agent = _agents[index % len(_agents)]
        index += 1

        messages = transcript.as_messages(for_agent_name=agent.name)

        try:
            turn = await agent.speak(messages)
        except asyncio.CancelledError:
            raise
        except Exception as e:
            await _broadcast({"type": "error", "message": str(e)})
            await asyncio.sleep(3)
            continue

        transcript.append(turn)
        await _broadcast({"type": "turn", "speaker": turn.speaker, "dialogue": turn.dialogue})

        # Brief pause so the UI has time to render and models aren't slammed
        await asyncio.sleep(0.3)


async def _start_loop() -> None:
    global _loop_task
    if _loop_task and not _loop_task.done():
        _loop_task.cancel()
        try:
            await _loop_task
        except asyncio.CancelledError:
            pass
    _loop_task = asyncio.create_task(_conversation_loop())


# ---------------------------------------------------------------------------
# App lifecycle
# ---------------------------------------------------------------------------

@asynccontextmanager
async def lifespan(app: FastAPI):
    await _start_loop()
    yield
    if _loop_task:
        _loop_task.cancel()


app = FastAPI(lifespan=lifespan)


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.websocket("/ws")
async def ws_endpoint(websocket: WebSocket) -> None:
    await websocket.accept()
    _connected.add(websocket)
    try:
        while True:
            # Just drain any keep-alive messages from the client
            await websocket.receive_text()
    except WebSocketDisconnect:
        _connected.discard(websocket)


@app.post("/reset")
async def reset() -> JSONResponse:
    await _broadcast({"type": "reset"})
    await _start_loop()
    return JSONResponse({"status": "ok"})


# Static files last so API routes take priority
app.mount("/", StaticFiles(directory="static", html=True), name="static")


# ---------------------------------------------------------------------------
# Entrypoint
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(description="agent-bar web server")
    parser.add_argument("--scene", default="config/scene.yaml")
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument("--host", default="127.0.0.1")
    args = parser.parse_args()

    global _scene, _agents
    _scene, _agents = _load_scene(args.scene)

    uvicorn.run(app, host=args.host, port=args.port)


if __name__ == "__main__":
    main()
