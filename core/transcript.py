from schemas.action import AgentTurn


class Transcript:
    """Append-only shared conversation buffer."""

    def __init__(self, setting: str = "", opening: str = ""):
        self.setting = setting
        self.opening = opening
        self._turns: list[AgentTurn] = []

    def append(self, turn: AgentTurn) -> None:
        self._turns.append(turn)

    def turns(self) -> list[AgentTurn]:
        return list(self._turns)

    def as_messages(self, for_agent_name: str) -> list[dict]:
        """
        Format the transcript as an OpenAI-style messages list from
        the perspective of the given agent (their turns = "assistant",
        everyone else = "user").
        """
        messages = []

        if self.setting or self.opening:
            preamble = []
            if self.setting:
                preamble.append(f"[Scene: {self.setting}]")
            if self.opening:
                preamble.append(self.opening)
            messages.append({"role": "user", "content": "\n".join(preamble)})

        for turn in self._turns:
            role = "assistant" if turn.speaker == for_agent_name else "user"
            content = f"{turn.speaker}: {turn.dialogue}"
            messages.append({"role": role, "content": content})

        return messages

    def contains_end_signal(self) -> bool:
        """Check if any agent has signalled end of scene."""
        return any("[END]" in turn.dialogue for turn in self._turns)

    def __len__(self) -> int:
        return len(self._turns)
