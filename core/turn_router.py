from core.agent import Agent
from core.transcript import Transcript


class TurnRouter:
    """
    Round-robin turn router for V1.

    Designed as a class so V3 can subclass it as HeartbeatRouter
    without changing the interface callers depend on.
    """

    def __init__(self, agents: list[Agent], max_turns: int = 30, min_turns: int = 8):
        self.agents = agents
        self.max_turns = max_turns
        self.min_turns = min_turns
        self._index = 0

    def next_agent(self) -> Agent:
        agent = self.agents[self._index % len(self.agents)]
        self._index += 1
        return agent

    def should_stop(self, transcript: Transcript) -> bool:
        if len(transcript) >= self.max_turns:
            return True
        if len(transcript) >= self.min_turns and transcript.contains_end_signal():
            return True
        return False
