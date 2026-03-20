from schemas.action import AgentTurn
from core.provider.base import BaseProvider


class AnthropicProvider(BaseProvider):
    """
    Stub — wired up in V2.

    When implemented, this will call the Anthropic Messages API.
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
            "AnthropicProvider is a V2 feature. "
            "Set provider: ollama in your persona config for V1."
        )
