from pydantic import BaseModel
from typing import List, Optional

class ChatMessage(BaseModel):
    role: str
    text: str

class ChatRequest(BaseModel):
    message: str
    game_id: str
    history: List[ChatMessage] = []

class TeamAnalyzeRequest(BaseModel):
    game_id: str
    characters: List[str]
