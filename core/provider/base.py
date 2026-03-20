from abc import ABC, abstractmethod
from schemas.action import AgentTurn


class BaseProvider(ABC):
    @abstractmethod
    async def complete(
        self,
        system_prompt: str,
        messages: list[dict],
        persona: dict,
    ) -> AgentTurn:
        """
        Generate the next agent turn.

        Args:
            system_prompt: The agent's system/character prompt.
            messages: Conversation history as [{role, content}, ...].
            persona: Full persona config dict — V2 will use this for
                     relationship context and other extended metadata.

        Returns:
            AgentTurn with at minimum speaker + dialogue populated.
        """
        pass
