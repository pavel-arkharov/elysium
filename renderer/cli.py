from rich.console import Console
from rich.text import Text
from rich.panel import Panel
from rich.rule import Rule
from schemas.action import AgentTurn

console = Console()

# Cycle through these for each unique speaker
_SPEAKER_COLORS = [
    "cyan",
    "magenta",
    "yellow",
    "green",
    "blue",
    "red",
    "bright_cyan",
    "bright_magenta",
]


class CLIRenderer:
    def __init__(self):
        self._color_map: dict[str, str] = {}
        self._color_index = 0

    def _color_for(self, speaker: str) -> str:
        if speaker not in self._color_map:
            self._color_map[speaker] = _SPEAKER_COLORS[
                self._color_index % len(_SPEAKER_COLORS)
            ]
            self._color_index += 1
        return self._color_map[speaker]

    def print_scene_header(self, title: str, setting: str, opening: str) -> None:
        console.print()
        console.print(Rule(f"[bold white]{title}[/bold white]"))
        if setting:
            console.print(f"[dim]{setting}[/dim]")
        if opening:
            console.print(f"\n[italic]{opening}[/italic]")
        console.print()

    def print_turn(self, turn: AgentTurn) -> None:
        color = self._color_for(turn.speaker)
        label = Text(f"{turn.speaker}", style=f"bold {color}")
        body = Text(f"  {turn.dialogue}", style="white")
        console.print(label)
        console.print(body)
        console.print()

    def print_end(self, reason: str) -> None:
        console.print(Rule(f"[dim]{reason}[/dim]"))
        console.print()

    def print_saved(self, path: str) -> None:
        console.print(f"[dim]Transcript saved → {path}[/dim]")
