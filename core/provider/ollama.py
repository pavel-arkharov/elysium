import httpx
from schemas.action import AgentTurn
from core.provider.base import BaseProvider


OLLAMA_BASE_URL = "http://localhost:11434"


class OllamaProvider(BaseProvider):
    def __init__(self, base_url: str = OLLAMA_BASE_URL):
        self.base_url = base_url

    async def complete(
        self,
        system_prompt: str,
        messages: list[dict],
        persona: dict,
    ) -> AgentTurn:
        model = persona["model"]
        max_tokens = persona.get("max_tokens", 150)

        payload = {
            "model": model,
            "messages": [{"role": "system", "content": system_prompt}] + messages,
            "stream": False,
            "think": False,
            "options": {
                "num_predict": max_tokens,
            },
        }

        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(
                f"{self.base_url}/api/chat",
                json=payload,
            )
            response.raise_for_status()

        data = response.json()
        content = data["message"]["content"].strip()

        # Strip any stage directions the model may have added (e.g. *nods*)
        # Keep only the first continuous block of quoted or plain dialogue
        dialogue = _clean_dialogue(content, persona["name"])

        return AgentTurn(speaker=persona["name"], dialogue=dialogue)


def _clean_dialogue(text: str, speaker: str) -> str:
    """Remove stage directions and any leading 'Speaker:' prefixes the model adds."""
    import re
    lines = text.splitlines()
    cleaned = []
    for line in lines:
        stripped = line.strip()
        # Drop pure stage direction lines: *action* or (action)
        if re.match(r"^\*[^*]+\*$", stripped) or re.match(r"^\([^)]+\)$", stripped):
            continue
        # Strip all leading "Name: " repetitions the model may prepend
        while re.match(rf"^{re.escape(speaker)}\s*:\s*", stripped, flags=re.IGNORECASE):
            stripped = re.sub(rf"^{re.escape(speaker)}\s*:\s*", "", stripped, flags=re.IGNORECASE)
        # Remove any inline [CHEERS] that appears mid-sentence (not as a standalone signal)
        if stripped and stripped != "[CHEERS]":
            stripped = re.sub(r"\[END\]", "", stripped).strip()
        cleaned.append(stripped)
    return "\n".join(cleaned).strip()
