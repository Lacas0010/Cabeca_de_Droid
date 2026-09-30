from pydantic import BaseModel
from typing import Dict, Any, Optional

class BreakpointRequest(BaseModel):
    game_id: Optional[str] = "hsr"
    char_name: str
    stats: Dict[str, Any]
