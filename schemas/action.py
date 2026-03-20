from pydantic import BaseModel
from typing import Optional


class AgentTurn(BaseModel):
    speaker: str
    dialogue: str
    # V2 will add:
    # physical_action: Optional[PhysicalAction] = None
    # internal_state: Optional[str] = None
