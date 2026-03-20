from core.provider.base import BaseProvider
from core.provider.ollama import OllamaProvider
from core.provider.anthropic import AnthropicProvider
from core.provider.openai import OpenAIProvider
from schemas.action import AgentTurn


_PROVIDER_MAP = {
    "ollama": OllamaProvider,
    "anthropic": AnthropicProvider,
    "openai": OpenAIProvider,
}


class Agent:
    def __init__(self, persona: dict):
        self.persona = persona
        self.name: str = persona["name"]
        self.system_prompt: str = persona["system_prompt"]
        self.provider: BaseProvider = self._build_provider(persona["provider"])

    def _build_provider(self, provider_name: str) -> BaseProvider:
        cls = _PROVIDER_MAP.get(provider_name)
        if cls is None:
            raise ValueError(
                f"Unknown provider '{provider_name}'. "
                f"Available: {list(_PROVIDER_MAP.keys())}"
            )
        return cls()

    async def speak(self, messages: list[dict]) -> AgentTurn:
        """Generate this agent's next turn given conversation history."""
        return await self.provider.complete(
            system_prompt=self.system_prompt,
            messages=messages,
            persona=self.persona,
        )
