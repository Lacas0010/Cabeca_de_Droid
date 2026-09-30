from pydantic import BaseModel

class FarmOrderToggleRequest(BaseModel):
    game_id: str
    task_id: str
    completed: bool = True

class FarmOrderSendNotificationRequest(BaseModel):
    game_id: str

class MaterialsCalculateRequest(BaseModel):
    game_id: str
    char_name: str
    current_level: int
    target_level: int
