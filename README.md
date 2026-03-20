# Elysium

A multi-agent dialogue simulator where LLM-powered characters talk to each other inside a shared scene — no human input required after setup.

Each agent is defined entirely through a YAML persona file: name, backstory, speaking style, and which LLM provider to use. Drop them into a scene config, start the server, and watch the conversation unfold in a browser or terminal.

---

## Why I built this

I wanted to explore how much of a believable character emerges from prompting alone, without any scripted dialogue or hard-coded behavior. The answer: quite a bit, especially when agents can read the full conversation history and respond to each other in context.

The secondary goal was an architecture that stays clean as complexity grows — so the turn routing, provider abstraction, and transcript are all separate layers designed to support future extensions (async agents, physical actions, narrator passes) without rewriting the core.

---

## How it works

1. You define one or more personas in YAML — each gets a system prompt, a provider (`ollama`, `openai`, or `anthropic`), and a model name.
2. A scene config sets the location, opening line, and the cast.
3. The `TurnRouter` walks through agents round-robin, feeding each the full conversation history formatted from their own perspective.
4. Every turn is broadcast over WebSocket to connected browsers and appended to an in-memory transcript.
5. Agents can signal end-of-scene by emitting `[END]` on a standalone line; otherwise the scene runs to `max_turns`.

---

## Stack

- **Python 3.11+** — async throughout (FastAPI + asyncio)
- **Ollama** — local model inference, no API key needed for default setup
- **FastAPI + WebSocket** — streaming turns to the browser in real time
- **Pydantic** — typed turn schema (`AgentTurn`) shared across all layers
- **YAML** — all scene and persona configuration, nothing hardcoded

---

## Running it

**Prerequisites:** Python 3.11+, [Ollama](https://ollama.com) running locally with at least one model pulled (e.g. `ollama pull llama3`).

```bash
pip install -r requirements.txt

# Web interface (default)
python server.py

# CLI mode
python main.py
```

Open `http://localhost:8000` — the scene starts automatically and streams each line as it's generated.

---

## Project structure

```
config/
  scene.yaml          # scene settings and cast list
  personas/           # one YAML file per agent
core/
  agent.py            # wraps a persona + provider into a speaking agent
  transcript.py       # append-only conversation buffer
  turn_router.py      # decides whose turn it is and when to stop
  provider/           # BaseProvider + Ollama / OpenAI / Anthropic adapters
schemas/
  action.py           # AgentTurn — the shared data contract
renderer/
  cli.py              # Rich-based terminal renderer
server.py             # FastAPI entrypoint, WebSocket broadcast
main.py               # CLI entrypoint
```

---

## Extending it

The architecture is deliberately layered so extensions don't require rewriting existing code:

- **New provider** — subclass `BaseProvider`, register in `agent.py`
- **New turn logic** — subclass `TurnRouter` (e.g. priority-based, heartbeat)
- **New fields on a turn** — extend `AgentTurn` in `schemas/action.py`
- **New renderer** — consume `Transcript.turns()` however you like
