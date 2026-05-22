# Elysium

**Autonomous multi-agent dialogue simulator exploring character emergence. Built with Python and FastAPI, supporting local (Ollama) and cloud (OpenAI) models with real-time WebSocket streaming.**

---

## 🎭 The Project

Elysium is a zero-human-input conversation engine where LLM-powered personas interact within simulated scenes. Instead of scripted dialogue, characters emerge through rigorous system prompting and contextual awareness. Each agent reads the full conversation history and responds in character, leading to unpredictable and often profound dialogue.

## 🛠️ Technical Highlights

### 1. Provider Abstraction (Strategy Pattern)
The architecture decouples the core agent logic from specific LLM implementations. By using a `BaseProvider` interface, the system seamlessly switches between:
- **Local Inference**: via Ollama (no API keys required).
- **Cloud Scale**: via OpenAI.
New providers can be added by simply subclassing `BaseProvider` and registering them in the `Agent` factory.

### 2. Async-First Core
Built on **Python 3.11+** and **FastAPI**, the engine is fully asynchronous. This ensures that long-running LLM completions do not block the WebSocket broadcast loop or the CLI renderer, providing a smooth real-time experience.

### 3. Shared Data Contracts
All turns are serialized using **Pydantic** models (`AgentTurn`). This ensures a single source of truth for the data schema, shared across:
- The `TurnRouter` (logic layer)
- The `Transcript` (data layer)
- The Web UI (presentation layer)

### 4. Dynamic Scene Injection
The `server.py` implements a Jeopardy-style topic system (`topics.yaml`). At the start of each scene, a random category and point value are selected, injecting a specific "seed" into the conversation to steer the agents' initial interaction.

## 🏗️ Project Structure

```text
config/
  scene.yaml          # Scene settings and initial cast
  topics.yaml         # Dynamic conversation seeds (Jeopardy-style)
  personas/           # Agent definitions (Name, Backstory, Provider)
core/
  agent.py            # Agent factory and logic
  transcript.py       # Async-safe conversation buffer
  turn_router.py      # Strategic turn management
  provider/           # Strategy-based LLM adapters
schemas/
  action.py           # Pydantic data contracts
renderer/
  cli.py              # Rich-powered terminal UI
server.py             # FastAPI/WebSocket entrypoint
main.py               # CLI entrypoint
```

## 🚀 Getting Started

### Prerequisites
- Python 3.11+
- [Ollama](https://ollama.com) (for local models, e.g., `llama3`)

### Installation
1. Clone the repo and enter the directory.
2. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows use `venv\Scripts\activate`
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

### Running the Simulation
**Web Interface (Real-time Broadcast):**
```bash
python server.py
```
*Open `http://localhost:8000` to watch the conversation unfold.*

**Terminal Mode:**
```bash
python main.py
```

---

## 🧠 Design Philosophy

The core goal of Elysium was to explore **emergent behavior**. By moving away from hard-coded state machines and towards prompt-driven autonomy, the project demonstrates how much "believability" can be generated through pure LLM context management. The architecture was designed to be modular, allowing for future extensions like physical actions, narrator passes, and complex turn-routing logic without core refactoring.
