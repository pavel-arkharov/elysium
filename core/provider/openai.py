from schemas.action import AgentTurn
from core.provider.base import BaseProvider


class OpenAIProvider(BaseProvider):
    """
    Stub — wired up in V2.

    When implemented, this will call the OpenAI Chat Completions API.
    The full persona dict is passed so V2 can inject relationship
    context and other metadata into the system prompt.
    """

    async def complete(
        self,
        system_prompt: str,
        messages: list[dict],
        persona: dict,
    ) -> AgentTurn:
        raise NotImplementedError(
            "OpenAIProvider is a V2 feature. "
            "Set provider: ollama in your persona config for V1."
        )
