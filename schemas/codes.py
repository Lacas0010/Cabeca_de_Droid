from pydantic import BaseModel
from typing import Optional

class RedeemCodeRequest(BaseModel):
    game_id: str
    code: Optional[str] = None
