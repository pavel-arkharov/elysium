#!/usr/bin/env python3
"""
agent-bar — CLI multi-agent dialogue simulator
Usage:
    python main.py --scene config/scene.yaml
    python main.py --scene config/scene.yaml --max-turns 20
    python main.py --scene config/scene.yaml --persona config/personas/custom.yaml
"""

import argparse
import asyncio
import json
import os
import sys
from datetime import datetime
from pathlib import Path

import yaml

from core.agent import Agent
from core.transcript import Transcript
from core.turn_router import TurnRouter
from renderer.cli import CLIRenderer


def load_yaml(path: str | Path) -> dict:
    with open(path) as f:
        return yaml.safe_load(f)


def load_scene(scene_path: str, extra_persona: str | None, max_turns_override: int | None) -> tuple[dict, list[dict]]:
    scene_dir = Path(scene_path).parent
    scene = load_yaml(scene_path)

    # Load cast from scene, with optional extra persona injected
    persona_paths = scene.get("cast", [])
    if extra_persona:
        persona_paths = list(persona_paths) + [extra_persona]

    personas = []
    for p in persona_paths:
        # Paths in cast are relative to config/ dir
        full_path = scene_dir / p
        personas.append(load_yaml(full_path))

    if max_turns_override is not None:
        scene["max_turns"] = max_turns_override

    return scene, personas


def save_transcript(transcript: Transcript, scene: dict) -> str:
    os.makedirs("output", exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = f"output/session_{timestamp}.json"

    data = {
        "scene": scene.get("title", ""),
        "setting": scene.get("setting", ""),
        "opening": scene.get("opening", ""),
        "turns": [t.model_dump() for t in transcript.turns()],
    }

    with open(path, "w") as f:
        json.dump(data, f, indent=2)

    return path


async def run(scene_path: str, extra_persona: str | None, max_turns_override: int | None) -> None:
    scene, personas = load_scene(scene_path, extra_persona, max_turns_override)

    if not personas:
        print("Error: no personas defined in scene cast.", file=sys.stderr)
        sys.exit(1)

    agents = [Agent(p) for p in personas]
    transcript = Transcript(
        setting=scene.get("setting", ""),
        opening=scene.get("opening", ""),
    )
    router = TurnRouter(agents=agents, max_turns=scene.get("max_turns", 30))
    renderer = CLIRenderer()

    renderer.print_scene_header(
        title=scene.get("title", "Untitled"),
        setting=scene.get("setting", ""),
        opening=scene.get("opening", ""),
    )

    stop_reason = "Scene ended."

    while not router.should_stop(transcript):
        agent = router.next_agent()
        messages = transcript.as_messages(for_agent_name=agent.name)

        try:
            turn = await agent.speak(messages)
        except Exception as e:
            print(f"\n[Error from {agent.name}: {e}]", file=sys.stderr)
            stop_reason = f"Error: {e}"
            break

        transcript.append(turn)
        renderer.print_turn(turn)

        if transcript.contains_end_signal():
            stop_reason = "An agent ended the scene."
            break

    if len(transcript) >= router.max_turns:
        stop_reason = f"Reached max turns ({router.max_turns})."

    renderer.print_end(stop_reason)

    saved_path = save_transcript(transcript, scene)
    renderer.print_saved(saved_path)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="agent-bar: multi-agent LLM dialogue simulator"
    )
    parser.add_argument(
        "--scene",
        default="config/scene.yaml",
        help="Path to scene YAML (default: config/scene.yaml)",
    )
    parser.add_argument(
        "--max-turns",
        type=int,
        default=None,
        help="Override max turns from scene config",
    )
    parser.add_argument(
        "--persona",
        default=None,
        help="Path to an additional persona YAML to inject into the cast",
    )
    args = parser.parse_args()

    asyncio.run(run(args.scene, args.persona, args.max_turns))


if __name__ == "__main__":
    main()
