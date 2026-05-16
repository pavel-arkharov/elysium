#!/usr/bin/env python3
"""
server.py — FastAPI entrypoint for agent-bar web interface.

Usage:
    python3 server.py
    python3 server.py --scene config/scene.yaml --port 8000
"""

import argparse
import asyncio
import random
from contextlib import asynccontextmanager
from pathlib import Path

import uvicorn
import yaml
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from core.agent import Agent
from core.transcript import Transcript, _is_end_signal


# ---------------------------------------------------------------------------
# Global state
# ---------------------------------------------------------------------------

_connected: set[WebSocket] = set()
_loop_task: asyncio.Task | None = None
_scene: dict = {}
_agents: list[Agent] = []
_topics: dict = {}
_current_scene_msg: dict = {}  # replayed to late-joining clients


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


def _load_topics(topics_path: str) -> dict:
    with open(topics_path) as f:
        data = yaml.safe_load(f)
    return data.get("categories", {})


def _pick_topic() -> tuple[str, int, str]:
    """Returns (category, points, prompt)."""
    category = random.choice(list(_topics.keys()))
    points = random.choice(list(_topics[category].keys()))
    prompt = _topics[category][points]
    return category, int(points), prompt


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
    global _current_scene_msg
    category, points, topic_prompt = _pick_topic()

    opening = (
        f"{_scene.get('opening', '')}\n\nTonight's topic: {topic_prompt}"
    ).strip()

    transcript = Transcript(
        setting=_scene.get("setting", ""),
        opening=opening,
    )

    _current_scene_msg = {
        "type": "scene",
        "title": _scene.get("title", ""),
        "setting": _scene.get("setting", ""),
        "opening": _scene.get("opening", ""),
        "topic": topic_prompt,
        "category": category,
        "points": points,
    }
    await _broadcast(_current_scene_msg)

    index = random.randrange(len(_agents))
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

        # Auto-reset if enough agents have said [END] as a standalone signal
        end_count = sum(1 for t in transcript.turns() if _is_end_signal(t.dialogue))
        if end_count >= len(_agents):
            await _broadcast({"type": "cheers"})
            await asyncio.sleep(4)
            await _broadcast({"type": "reset"})
            await _start_loop()
            return

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
    # Replay current topic so late-joining clients see it immediately
    if _current_scene_msg:
        try:
            await websocket.send_json(_current_scene_msg)
        except Exception:
            pass
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        _connected.discard(websocket)


@app.post("/reset")
async def reset() -> JSONResponse:
    await _broadcast({"type": "reset"})
    await _start_loop()
    return JSONResponse({"status": "ok"})


app.mount("/", StaticFiles(directory="static", html=True), name="static")


# ---------------------------------------------------------------------------
# Entrypoint
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(description="agent-bar web server")
    parser.add_argument("--scene", default="config/scene.yaml")
    parser.add_argument("--topics", default="config/topics.yaml")
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument("--host", default="127.0.0.1")
    args = parser.parse_args()

    global _scene, _agents, _topics
    _scene, _agents = _load_scene(args.scene)
    _topics = _load_topics(args.topics)

    uvicorn.run(app, host=args.host, port=args.port)


if __name__ == "__main__":
    main()
